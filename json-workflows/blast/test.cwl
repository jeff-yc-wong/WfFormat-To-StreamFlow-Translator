cwlVersion: v1.2
class: Workflow
requirements:
  MultipleInputFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}

inputs:
  input_files:
    type: File[]

outputs:
  final_output_folder:
    type: Directory
    outputSource: final_folder/out

steps:
  step1:
    run:
      class: CommandLineTool
      baseCommand: /Users/wongy/Documents/GitHub/WfFormat-To-StreamFlow-Translator/json-workflows/blast/wfbench.py
      arguments: 
        - valueFrom: "split_fasta_00000001"
        - prefix: --percent-cpu
          valueFrom: "0.6"
        - prefix: --cpu-work
          valueFrom: "100"
      stdout: "output.txt"
      stderr: "error.txt"
      inputs:
        input_files:
          type: File[]
          inputBinding:
            position: 0
      outputs:
        example_out:
          type: stdout
        example_err:
          type: stderr
        file_out:
          type:
            type: array
            items:
              - File
          outputBinding:
            glob: "split_fasta*.txt"
    in:
      input_files: input_files
    out: [example_out, example_err, file_out]

  step1_folder:
    run: folder.cwl
    in:
      - id: item
        linkMerge: merge_flattened
        source:
          - step1/example_out
          - step1/example_err
          - step1/file_out
      - id: name
        valueFrom: "step1"
    out: [out]  

  step2:
    run: wfbench_v2.cwl
    in:
      input_params: {default: ["blastall_00000002", "--percent-cpu", "0.6", "--cpu-work", "100", "--out", "{'blastall_00000002_output.txt': 227273}"]}
      input_files:
        linkMerge: merge_flattened
        source: 
          - step1/file_out
        valueFrom: $(inputs.input_files.filter(file => /^split_fasta.*.txt/.test(file.basename)))
      step_name: 
        valueFrom: "blastall_00000002" # just replace with the task.name
      output_filenames:
        valueFrom: $(["blastall_00000002_output.txt"])
    out: [out, err, output_files]
  
  step2_folder:
    run: folder.cwl
    in:
      - id: item
        linkMerge: merge_flattened
        source:
          - step2/out
          - step2/err
          - step2/output_files
      - id: name
        valueFrom: "step2"
    out: [out]

  final_folder:
    run: folder.cwl
    in:
      - id: item
        linkMerge: merge_flattened
        source:
          - step1_folder/out
          - step2_folder/out 
      - id: name
        valueFrom: "final_output"
    out: [out]  

