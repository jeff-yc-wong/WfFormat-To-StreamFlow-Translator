import pathlib

from wfcommons import BlastRecipe
from wfcommons.wfbench import WorkflowBenchmark, DaskTranslator
from wfcommons import MontageRecipe


# create a workflow benchmark object to generate specifications based on a recipe
benchmark = WorkflowBenchmark(recipe=BlastRecipe, num_tasks=45)
# generate a specification based on performance characteristics
path = benchmark.create_benchmark(pathlib.Path("./blast_base"), cpu_work=100, data=10, percent_cpu=0.6)

# create a workflow benchmark object to generate specifications based on a Montage recipe
benchmark = WorkflowBenchmark(recipe=MontageRecipe, num_tasks=60)
# generate a specification based on performance characteristics
path = benchmark.create_benchmark(pathlib.Path("./montage"), cpu_work=100, data=10, percent_cpu=0.6)


# generate a Pegasus workflow
translator = DaskTranslator(benchmark.workflow)
translator.translate(output_folder=pathlib.Path("/tmp/benchmark-workflow.py"))
