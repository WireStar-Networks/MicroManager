# MicroManager
Debug tools for management and diagnostics on TeamlyDigital Micronodes. 

## Installation

1. Go to the repository homepage (if you're reading this, you're probably already there).
2. Click the "Code" button (usually a green button).
3. Select "Download ZIP" from the dropdown menu.
4. Save the ZIP file to your local machine.
5. Extract (unzip) the contents into a directory of your choice.
6. You should see a folder containing the script `parse_cnu.py`. You'll need this location to run the script. 

## Usage

1. Open a terminal, command prompt, PowerShell, etc.

> **_NOTE:_** ⚠️ You MUST replace the path below with your actual path. The following is merely a placeholder path for demonstration only. 

2. Change directories to the folder where you extracted the script. For example:
    ```cmd
    cd \path\to\my\extracted\folder
3. Create a text file and paste the micronode output, preferably without unnecessary lines/spaces. You may also use the template file provided `log.txt`.
4. Run the script using Python. An input file argument is mandatory (ex: `log.txt`). To see all options, run the following command:
    ```cmd
    python parser.py --help
