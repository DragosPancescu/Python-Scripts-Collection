"""
Extracts arguments and variables from an UiPath project, dumps them into an YAML file
"""

import re
import os
import yaml
import sys
import math

from collections import OrderedDict

# Regular expressions
FULL_TAG_RE = re.compile('((x:Property|Variable x:TypeArguments=).*)')
NAME_RE = re.compile('(?<=Name=\")((in|out|io)_\w+|\w+)')
ANNOTATION_RE = re.compile('(?<=AnnotationText=\")[\w\s,\.;:\-_()]+')


def main(input_directory: str, output_file: str):

    # Used for writing to output yaml file
    yaml_dict = {'DU_Annotations': []}

    for workflow_file in os.listdir(input_directory):
        workflow_dict = {workflow_file: {'Arguments': [], 'Variables': []}}

        with open(os.path.join(input_directory, workflow_file), 'r') as f:
            content = f.read()

            # Find full tag for all arguments and variables
            full_tags = FULL_TAG_RE.findall(content)

            # For each find we extract the name and annotation
            for tag in full_tags:
                name = NAME_RE.search(tag[0]).group(0)
                annotation = ANNOTATION_RE.search(tag[0]).group(0)

                info = OrderedDict([('Name', name), ('Annotation', annotation)])

                # Check if it is a variable or an argument
                if any(re.findall('(in|out|io)_', name)):
                    workflow_dict[workflow_file]['Arguments'].append(dict(info))
                else:
                    workflow_dict[workflow_file]['Variables'].append(dict(info))
        
        # Checks if there are no variables/arguments present in the workflow
        if len(workflow_dict[workflow_file]['Arguments']) == 0:
            workflow_dict[workflow_file]['Arguments'].append('N/A')
            
        if len(workflow_dict[workflow_file]['Variables']) == 0:
            workflow_dict[workflow_file]['Variables'].append('N/A')

        yaml_dict['DU_Annotations'].append(workflow_dict)

    with open(output_file, 'w') as f:
        yaml.dump(yaml_dict, f, sort_keys=False, width=math.inf)


if __name__ == "__main__":

    input_directory = str(sys.argv[1])
    output_file = str(sys.argv[2])

    main(input_directory, output_file)