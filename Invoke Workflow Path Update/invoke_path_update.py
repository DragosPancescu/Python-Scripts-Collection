""" 
Goes through all the invoke workflows in an UiPath project and updates the paths with whatever files it finds in the project tree
"""

import os
import re
import sys


def get_absolute_filenames(path: str) -> list[str]:
    """
    Returns the full paths of the files (XAMLs) found in a given folder.
    :param path: The full path of the folder containing the data
    :return: List of absolute filenames
    """
    absolute_filenames = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.split(".")[-1].lower() != "xaml":
                continue
            absolute_filenames.append(os.path.join(root, file))

    return absolute_filenames


def get_folder_names(folder_name: str) -> list[str]:
    """
    Returns the first level folders found in a given folder
    :param folder_name: Folder name in the project
    :return: List of folder names
    """
    top_level_folder_names = filter(os.path.isdir, [os.path.join(
        folder_name, f) for f in os.listdir(folder_name)])
    top_level_folder_names = [f.split("\\")[-1] for f in top_level_folder_names]

    return top_level_folder_names


def build_folder_regex(top_level_folder_name: list[str]) -> list[str]:
    """
    Builds a regex that matches a top level folder (and all the previous parts of the path) in an invoke path
    :param top_level_folder_name: List of folder names
    :return: List of regex patterns
    """
    regex_patterns = []
    for folder in top_level_folder_name:
        regex_patterns.append(f"(?<=WorkflowFileName=).*(?={folder}\\\\)")

    return regex_patterns


def update_all_invoke_paths(absolute_filenames: list[str], regex_patterns: list[str], converted_folder_name: str) -> int:
    """
    Updates all the invoke workflow paths so that they point to the converted folder
    :param absolute_filenames: List of absolute filenames
    :param regex_patterns: List of regex patterns
    :param converted_folder_name: Name of the converted folder used for updating the paths
    :return: Number of updated paths
    """
    count = 0
    for filename in absolute_filenames:
        with open(filename, "r") as f:
            file_data = f.read()

        for regex in regex_patterns:
            count += len(re.findall(regex, file_data))
            file_data = re.sub(regex, f"\"{converted_folder_name}\\\\", file_data)

        with open(filename, "w") as f:
            f.write(file_data)

    return count


# python3 invoke_path_update.py <path_to_project_folder>
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise TypeError(
            "\nWrong number of parameters, only one is needed (Path to the UiPath Studio project)")

    project_path = str(sys.argv[1])
    converted_folder_name = "Converted"

    absolute_filenames = get_absolute_filenames(project_path)
    folder_names = get_folder_names(
        os.path.join(project_path, converted_folder_name))
    regex_patterns = build_folder_regex(folder_names)

    count = 0
    try:
        count = update_all_invoke_paths(
            absolute_filenames, regex_patterns, converted_folder_name)
    except PermissionError:
        print(PermissionError.strerror)

    print(f"Updated {count} invoke workflow paths.")
