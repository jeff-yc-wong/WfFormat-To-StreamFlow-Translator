import json
import shutil
import re
import logging
from typing import Dict, Union, List, Optional
from wfcommons.common import FileLink, Task, Workflow
# from .abstract_translator import Translator
# from ...common import FileLink, Workflow
from wfcommons.wfinstances import Instance
from abstract_translator import Translator
from collections import defaultdict, deque
import pathlib
import argparse
from itertools import islice
from pathlib import Path

# this_dir = pathlib.Path(__file__).resolve().parent


class StreamFlowTranslator(Translator):
    # output_path/
    # │
    # ├── cwl/
    # │   ├── main.cwl
    # │   ├── config.yml
    # │
    # ├── environment
    # │   ├── streamflow.yml
    # │
    # ├── streamflow.yml

    def __init__(self,
                 workflow: Union[Workflow, pathlib.Path],
                 logger: Optional[logging.Logger] = None) -> None:
        super().__init__(workflow, logger)
        self.cwl_script = ["cwlVersion: v1.2",
                           "class: Workflow",
                           "requirements:",
                           "  MultipleInputFeatureRequirement: {}",
                           "  StepInputExpressionRequirement: {}",
                           "  InlineJavascriptRequirement: {}"]
        self.yml_script = []
        self.parsed_tasks = []
        self.task_level_map = defaultdict(lambda: [])

        queue = deque(self.root_task_names)
        visited = set()
        top_sort = []

        while queue:
            task_name = queue.popleft()

            if task_name not in visited:
                top_sort.append(task_name)
                visited.add(task_name)

            for child in self.task_children[task_name]:
                queue.append(child)

        assert (len(top_sort) == len(self.tasks))

        levels = {task_name: 0 for task_name in top_sort}

        for task_name in top_sort:
            for child in self.task_children[task_name]:
                levels[child] = max(levels[child], levels[task_name] + 1)

        for task_name, level in levels.items():
            self.task_level_map[level].append(task_name)

    def translate(self, output_folder: pathlib.Path) -> None:
        # Parsing the inputs and outputs of the workflow
        self._parse_inputs_outputs()

        # Parsing the steos
        self._parse_steps()

        # additional files
        self._copy_binary_files(output_folder)
        self._generate_input_files(output_folder)

        # Writing the StreamFlow/CWL files to the output folder
        self._write_streamflow_files(output_folder)

        return 0

    def _parse_steps(self) -> None:
        steps_folder_source = []
        self.cwl_script.append("\nsteps:")
        # Parsing each steps by Workflow levels
        for level in sorted(self.task_level_map.keys()):
            # Parsing each task within a Workflow level
            for task_name in self.task_level_map[level]:

                # Getting the task object
                task = self.tasks[task_name]

                # Parsing the arguments of the task
                args_array = []
                benchmark_name = False

                for item in task.args:
                    # Split elements that contain both an option and a value
                    if item.startswith("--"):
                        parts = item.split(" ", 1)
                        args_array.append(parts[0])
                        if len(parts) > 1:
                            args_array.append(parts[1])
                    elif not benchmark_name:
                        args_array.append(item)
                        benchmark_name = True

                output_files = [
                    f.name for f in task.files if f.link == FileLink.OUTPUT]

                # Adding the step to the cwl script

                self.cwl_script.append(f"  {task.name}:")
                # TODO: change so that it doesn't only run wfbench programs
                if not task.program == "wfbench.py":
                    raise ValueError("Only wfbench programs are supported")
                self.cwl_script.append("    run: clt/wfbench.cwl")

                self.cwl_script.append("    in:")
                if level == 0:
                    self.cwl_script.append(
                        f"      input_files: {task.name}_input")
                else:
                    self.cwl_script.append(
                        "      input_files:")
                    self.cwl_script.append(
                        "        linkMerge: merge_flattened")
                    self.cwl_script.append(
                        "        source:")
                    for parent in self.task_parents[task_name]:
                        self.cwl_script.append(
                            f"          - {parent}/output_files")
                self.cwl_script.append(
                    f"      input_params: {{ default: {args_array} }}")
                self.cwl_script.append("      step_name:")
                self.cwl_script.append(f"        valueFrom: {task.name}")
                self.cwl_script.append(f"      output_filenames: {{ default: {output_files} }}")
                self.cwl_script.append(
                    "    out: [out, err, output_files]\n")

                # Adding a step to create a directory with the output files
                self.cwl_script.append(f"  {task.name}_folder:")
                self.cwl_script.append("    run: clt/folder.cwl")
                self.cwl_script.append("    in:")
                self.cwl_script.append("      - id: item")
                self.cwl_script.append("        linkMerge: merge_flattened")
                self.cwl_script.append("        source:")
                self.cwl_script.append(f"          - {task.name}/out")
                self.cwl_script.append(f"          - {task.name}/err")
                self.cwl_script.append(f"          - {task.name}/output_files")
                self.cwl_script.append("      - id: name")
                self.cwl_script.append(f"        valueFrom: \"{level}_{task.name}\"")
                self.cwl_script.append("    out: [out]\n")

                # adding the folder id to grand list of step folders
                steps_folder_source.append(f"{task.name}_folder")

        self.cwl_script.append("  final_folder:")
        self.cwl_script.append("    run: clt/folder.cwl")
        self.cwl_script.append("    in:")
        self.cwl_script.append("      - id: item")
        self.cwl_script.append("        linkMerge: merge_flattened")
        self.cwl_script.append("        source:")
        for folder in steps_folder_source:
            self.cwl_script.append(f"          - {folder}/out")
        self.cwl_script.append("      - id: name")
        self.cwl_script.append("        valueFrom: \"final_output\"")
        self.cwl_script.append("    out: [out]")

    def _parse_inputs_outputs(self) -> None:
        # Parsing the inputs of all root tasks
        self.cwl_script.append("\ninputs:")
        for task_name in self.root_task_names:
            task = self.tasks[task_name]
            cwl_written = False
            yml_written = False
            for f in task.files:
                if f.link == FileLink.INPUT:
                    if not cwl_written:
                        self.cwl_script.append(f"  {task.name}_input:")
                        self.cwl_script.append("    type: File[]")
                        cwl_written = True
                    if not yml_written:
                        self.yml_script.append(f"{task.name}_input:")
                        yml_written = True

                    self.yml_script.append("  - class: File")
                    self.yml_script.append(f"    path: ../data/{f.name}")

        # Appending the output to the cwl script
        self.cwl_script.append("\noutputs:")
        self.cwl_script.append("  final_output_folder:")
        self.cwl_script.append("    type: Directory")
        self.cwl_script.append("    outputSource: final_folder/out")

    def _write_streamflow_files(self, output_folder: pathlib.Path) -> None:
        cwl_folder = output_folder.joinpath("cwl")
        cwl_folder.mkdir(exist_ok=True)

        clt_folder = cwl_folder.joinpath("clt")
        clt_folder.mkdir(exist_ok=True)
        shutil.copy(Path.cwd().joinpath("templates/wfbench.cwl"), clt_folder)
        shutil.copy(Path.cwd().joinpath("templates/folder.cwl"), clt_folder)
        shutil.copy(Path.cwd().joinpath("templates/local.yml"), output_folder)

        with open(cwl_folder.joinpath("main.cwl"), "w", encoding="utf-8") as f:
            f.write("\n".join(self.cwl_script))

        with (open(cwl_folder.joinpath("config.yml"), "w", encoding="utf-8")) as f:
            f.write("\n".join(self.yml_script))

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "wfformat_file", help="path to WfFormat JSON input file")
    parser.add_argument("--outdir", default=Path.cwd().joinpath("output"),
                        help="Output directory in which to store the translated files")

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    wf_input = args.wfformat_file
    outdir_path = args.outdir

    if not isinstance(outdir_path, Path):
        outdir_path = Path(outdir_path)

    if not outdir_path.exists():
        outdir_path.mkdir(parents=True, exist_ok=True)

    try:
        instance = Instance(wf_input)
    except Exception as e:
        raise e

    workflow_obj = instance.workflow

    translator = StreamFlowTranslator(workflow_obj)

    translator.translate(output_folder=outdir_path)

    return 0


if __name__ == "__main__":
    main()