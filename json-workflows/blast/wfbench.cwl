cwlVersion: v1.2
class: CommandLineTool
baseCommand: /Users/wongy/Documents/GitHub/WfFormat-To-StreamFlow-Translator/json-workflows/blast/wfbench.py
stdout: output.txt
stderr: error.txt
inputs:
  name:
    type: string
    inputBinding:
      position: 0
  percent_cpu:
    type: float?
    inputBinding:
      prefix: --percent-cpu
      position: 0
  path_lock:
    type: string?
    inputBinding:
      prefix: --path-lock
      position: 1
  path_cores:
    type: string?
    inputBinding:
      prefix: --path-cores
      position: 2
  cpu_work:
    type: int?
    inputBinding:
      prefix: --cpu-work
      position: 3
  gpu_work:
    type: int?
    inputBinding:
      prefix: --gpu-work
      position: 4
  time:
    type: int?
    inputBinding:
      prefix: --time
      position: 5
  mem:
    type: int?
    inputBinding: 
      prefix: --mem
      position: 6
  out:
    type: string?
    inputBinding:
      prefix: --out
      position: 7
  input_files:
    type: File[]
    inputBinding:
      position: 8
outputs:
  example_err:
    type: stderr
  example_out:
    type: stdout
  file_out:
    type: 
      type: array
      items:
        - File
        - Directory
    outputBinding:
      glob: "*.txt"
