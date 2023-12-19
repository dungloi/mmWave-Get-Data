import os
import shutil


def clean_directory(directory_path):
    cli_log_file_path = os.path.join(directory_path, "CLI_LogFile.txt")
    if os.path.exists(cli_log_file_path):
        os.remove(cli_log_file_path)

    for root, dirs, files in os.walk(directory_path):
        for directory in dirs:
            if directory == "__pycache__" or directory == "Data" or directory == "Log":
                to_remove_path = os.path.join(root, directory)
                print(f"Removing {to_remove_path}")
                shutil.rmtree(to_remove_path)


if __name__ == "__main__":
    target_directory = os.getcwd()
    clean_directory(target_directory)
