cwlVersion: v1.2
class: Workflow
requirements:
  MultipleInputFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}

inputs:
  split_input_string:
    type: string
  input_files:
    type: File[]

outputs:
  final_output_folder:
    type: Directory
    outputSource: output_folder/out

steps:
  step1:
    run: wfbench.cwl
    in:
      name: {default: "split_fasta_00000001"}
      percent_cpu: {default: 0.6}
      cpu_work: {default: 100}
      out: {default: "{'split_fasta_00000001_output.txt': 227273}"}
      input_files: input_files
    out: [example_out, example_err, file_out]
  

  step2:
    run: wfbench.cwl
    in:
      name: {default: "blastall_00000002"}
      percent_cpu: {default: 0.6}
      cpu_work: {default: 100}
      out: {default: "{'blastall_00000002_output.txt': 227273}"}
      input_files:
        source:
          - step1/file_out
        valueFrom: $(inputs.step1.out.filter(function(file) { return file.basename == "split_fasta_00000001_output.txt"; })[0])
    out: [example_out, example_err, file_out]


  output_folder:
    run: folder.cwl
    in:
      - id: item
        linkMerge: merge_flattened
        source:
          - step1/example_out
          - step1/example_err
          - step1/file_out
      - id: name
        valueFrom: "final_output"
    out: [out]  
      # step2:
      #   run: wfbench.cwl
      #   in:
      #     percent_cpu: {default: 0.6}
      #     cpu_work: {default: 100}
      #     out: {default: "{'split_fasta_00000001_output.txt': 227273}"}
      #     input_files: {default: "{split_fasta_00000001_output.txt: 227273}"}
      #   out: [example_out, example_err, file_out]
