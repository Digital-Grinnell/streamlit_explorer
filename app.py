from pathlib import Path
from st_click_detector import click_detector as did_click
import os 
import streamlit as st
from loguru import logger

COLOR_1 = "#0088ff"
COLOR_2 = "#ff8800" 

LIST_STYLE = """<style>
    a:link, a:visited {
    background-color: #79797918;
    color: gray;
    padding: 0px 10px;
    text-align: left;
    text-decoration: none;
    display: column-count:5; }
    a:hover, a:active {
      background-color: #98989836; }
    </style>"""

LARGE = """<style>
    * { font-size: 1.3em; }
    </style>"""

@st.cache_data
# st.cache(lambda: st.session_state, allow_output_mutation=True)

def get_subfolders_and_files(folder_path):
    subfolders = [ ]
    files = [ ]

    folder_path = os.path.normpath(folder_path).replace("\\", "/")
    
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            # Check permissions
            if not os.access(item_path, os.R_OK):
                print(f"Permission denied for {item_path}")
                continue

            # Check symbolic link
            if os.path.islink(item_path):
                print(f"{item_path} is a symbolic link")
                continue

            if os.path.isdir(item_path):
                subfolders.append({"name": item, "path": os.path.normpath(item_path)})
            else:
                files.append({"name": item, "path": os.path.normpath(item_path)})

            # Sort the folders and files before returning
            sorted_sub = sorted(subfolders, key=lambda d: d['name'])
            sorted_files = sorted(files, key=lambda d: d['name'])

        return sorted_sub, sorted_files

    except PermissionError as e:
        st.info(e)
        return subfolders, files


def get_folder_list(folder_path):
    folder_list = [ ]
    current_path = ""
    current_path = folder_path.replace("\\", "/")
    split_drive = Path(current_path).parts
    folders = split_drive
    for folder in folders:
        current_path = os.path.join(current_path, folder)
        folder_list.append({"name": folder, "path": current_path})
    return folder_list


def generate_folder_links(folder_path):
    paths = state("crumbs")
    subfolders, files = get_subfolders_and_files(folder_path)
    crumbs = {crumb["name"]: crumb["path"] for crumb in paths}
    current_crumb = paths[-1]["name"]

    st.session_state["crumb_list"] = f'/'.join([f'<a href="#" id="{crumbs[crumb["name"]]}">{crumb["name"]}</a>' for crumb in paths[:-1]] + [f'{LARGE}{current_crumb}'])

    folder_links = {sub["name"]: sub["path"] for sub in subfolders}
    file_links = {file["name"]: file["path"] for file in files}

    folder_list = None
    files_list = None

    if len(subfolders) > 0:
        num_of_columns = 3
        
        folder_list = [
            f'<a href="#" id="{folder_links[subfolder["name"]]}">'
            f'{LIST_STYLE}<font color="{COLOR_2}">&#128194;</font> {subfolder["name"]}'
            f"</a>"
            for subfolder in subfolders
        ]
        
        files_list = [
            f'<a href="{file_links[file["name"]]}">'
            f'{LIST_STYLE}<font color="{COLOR_2}"> - </font> {file["name"]}'
            f"</a>"
            for file in files
        ]

    st.session_state["subdirs"] = "<br>".join(folder_list or [ ])
    st.session_state["files"] = "<br>".join(files_list or [ ])


def update_paths( ):
    my_path = st.session_state.get("my_path", os.getcwd( ))
    try:
        subfolders, files = get_subfolders_and_files(my_path)
        st.session_state["subfolders"] = subfolders
        st.session_state["files"] = files
    except Exception as e:
        st.exception(e)
    try:
        crumbs = get_folder_list(my_path)
        st.session_state["crumbs"] = crumbs
    except Exception as e:
        st.exception(e)


def update_from_crumb( ):
    # logger.info(f'crumb_list is: {state('crumb_list')}')
    click = did_click(state("crumb_list"), None)
    if click:
        logger.warning(f'crumb_list clicked: {click}')
        st.session_state["new_crumb"] = click
        if state("new_crumb"):
            update_paths( )
            st.session_state["run_again"] = True


def update_subdirs( ):
    # logger.info(f'subdirs is: {state('subdirs')}')
    click = did_click(state("subdirs"), None)
    logger.warning(f'subdirs click is: {click}')
    st.session_state["new_subfolder"] = click
    if state("new_subfolder"):
        update_paths( )
        st.session_state["run_again"] = True


def file_selected( ):
    # logger.info(f'files is: {state('files')}')
    click = did_click(state("files"), None)
    logger.warning(f'files click is: {click}')
    if click:
        st.session_state['selected_files'].append(click)
        update_paths( )
        st.session_state["run_again"] = True


def new_path( ):
    current_path = st.session_state.get("my_path", os.getcwd( ))
    new_crumb = st.session_state.get("new_crumb")
    new_subfolder = st.session_state.get("new_subfolder")
    if new_crumb:
        st.session_state["new_crumb"] = None
        st.session_state["new_path"] = new_crumb
    elif new_subfolder:
        st.session_state["new_path"] = new_subfolder
    else:
        st.session_state["new_path"] = current_path


def update_new_path( ):
    new_path( )
    update_paths( )
    generate_folder_links(state("new_path"))
    update_from_crumb( )
    update_subdirs( )
    file_selected( )
    new_path( )
    return state("new_path")


# state(key) - Return the value of st.session_state[key] or False
# If state is set and equal to "None", return False.
# -------------------------------------------------------------------------------
def state(key):
    try:
        if st.session_state[key]:
            if st.session_state[key] == "None":
                return False
            return st.session_state[key]
        else:
            return False
    except Exception as e:
        # st.exception(f"Exception: {e}")
        return False


# MAIN ---------------------------------------------------------

if __name__ == '__main__':

    # Initialize the session_state
    if not state('logger'):
        logger.add("app.log", rotation="500 MB")
        logger.info('This is streamlit_explorer/app.py!')
        st.session_state.logger = logger
    if not state('selected_files'):
        st.session_state.selected_files = [ ]
    if not state('remove_path_levels'):
        st.session_state.remove_path_levels = 4
    
    # Add a sidebar for control and display.
    with st.sidebar:

        # Monitor new_path
        if state('new_path'):
            st.success(f"new_path is: {state('new_path')}")

        # List of selected files...
        st.write("Selected files:")
        if state('selected_files'):
            for file in state('selected_files'):
                st.write(file)
        else:
            st.warning("None")

    st.session_state["my_path"] = update_new_path( )

    if state("run_again"):
        st.session_state["run_again"] = False
        update_paths( )
        state("my_path")
        st.rerun( )

    state("my_path")
