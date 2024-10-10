from pathlib import Path
from st_click_detector import click_detector as did_click
import os 
import streamlit as st
from loguru import logger
import frontmatter

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

# @st.cache_data
# st.cache(lambda: st.session_state, allow_output_mutation=True)

# File Select functions from https://github.com/Digital-Grinnell/streamlit_explorer
# -------------------------------------------------------------------------------------

def get_subfolders_and_files(folder_path):
    subfolders = [{"name":"..", "path":str(Path(folder_path).parent)}]
    files = [ ]

    folder_path = os.path.normpath(folder_path).replace("\\", "/")
    
    try:

        regex = state('file_regex')

        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            # Check permissions
            if not os.access(item_path, os.R_OK):
                logger.warning(f"Permission denied for {item_path}")
                continue

            # Check symbolic link
            if os.path.islink(item_path):
                logger.warning(f"{item_path} is a symbolic link")
                continue

            # Check hidden
            if not state('show_hidden'):
                base = os.path.basename(item_path)
                if base.startswith('.'):
                    # logger.warning(f"{item_path} is hidden and will not be displayed")
                    continue

            if os.path.isdir(item_path):
                subfolders.append({"name": item, "path": os.path.normpath(item_path)})

            else:
                extension = os.path.splitext(item_path)[1]
                if (not regex) or (extension == regex):
                    files.append({"name": item, "path": os.path.normpath(item_path)})

            # Sort the folders and files before returning
            sorted_sub = sorted(subfolders, key=lambda d: d['name'])
            sorted_files = sorted(files, key=lambda d: d['name'])

        return sorted_sub, sorted_files

    except PermissionError as e:
        st.info(e)
        return subfolders, files
    except Exception as e:
        st.exception(e)

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
        
        # Rebuild the files_list showing selected files with a checkmark.
        files_list = [ ]
        selected = state('selected_files')

        for file in files:
            if selected and (file["path"] in selected):
                symbol = " &#10004; "
            else: 
                symbol = " - "
            files_list.append(f'<a href="#" id="{file_links[file["name"]]}">'
            f'{LIST_STYLE}<font color="{COLOR_2}">{symbol}</font> {file["name"]}'
            f"</a>")

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
        # logger.warning(f'crumb_list clicked: {click}')
        st.session_state["new_crumb"] = click
        if state("new_crumb"):
            update_paths( )
            st.session_state["run_again"] = True

def update_subdirs( ):
    # logger.info(f'subdirs is: {state('subdirs')}')
    click = did_click(state("subdirs"), None)
    # logger.warning(f'subdirs click is: {click}')
    st.session_state["new_subfolder"] = click
    if state("new_subfolder"):
        update_paths( )
        st.session_state["run_again"] = True

def file_selected( ):
    # logger.info(f'files is: {state('files')}')
    if state('files'):
      click = did_click(state("files"), None)
      # logger.warning(f'files click is: {click}')
      if click:

          selected = state('selected_files')

          # Append the selection to our list
          if click not in selected:
              st.session_state['selected_files'].append(click)       
            
          # Remove the selection from our list    
          else:
              st.session_state['selected_files'].remove(click)       
            
          update_paths( )
          st.session_state["run_again"] = True

    else: 
        st.write(f"There are NO files to select from.")
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
    if state('mode') == 'select':
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

def clear_selected_files( ):
    st.session_state.selected_files = ["."]

# --- End of File Select functions from https://github.com/Digital-Grinnell/streamlit_explorer
# ----------------------------------------------------------------------------------


# line_open_and_close(filename)   
# ...from https://stackoverflow.com/questions/5914627/prepend-line-to-beginning-of-a-file
# -----------------------------------------------------------------------------
def line_open_and_close(filename, prefix):

    path = filename
    if state('remove_path_levels'):
        num = state('remove_path_levels')
        parts = filename.split('/')
        remove = '/'.join(parts[:num]) + '/'
        path = filename.replace(remove, '')    

    # Build the tags
    tag1 = f"<!-- {prefix} {path} -->"
    tag2 = tag1.replace(prefix, "/" + prefix)

    # Assume frontmatter is present, wrap 'content' portion of file with tags
    with open(filename, 'r+') as f:
        fmc = frontmatter.load(f)
        # (metadata, content) = frontmatter.parse(f.read( ))
        final = tag1.rstrip('\r\n') + '\n' + fmc.content + '\n' + tag2.rstrip('\r\n')
        fmc.content = final
        if fmc.metadata:
            complete = frontmatter.dumps(fmc)
            logger.info(f"Inserted tag '{tag1}' following {path} frontmatter")
        else:
            complete = final
            logger.info(f"No frontmatter detected, tag '{tag1}' prepended to {path}")
        f.seek(0, 0)
        f.write(complete)
        f.close( )

        logger.info(f"Appended tag '{tag2}' to end of {path}")


# go_for_processing( ) - The guts of the app after files have been selected. Git 'er done!
# -------------------------------------------------------------------------------
def go_for_processing( ):

    prefix = state('tag_prefix')

    st.session_state.mode = 'processing'
    page = st.empty( )
    count = 0

    with page.container(key='process-container'):
        msg = f"This is 'go_for_processing'!"
        logger.info(msg)
        st.warning(msg)

        # Open each file, make additions and display it briefly, them move on to the next
        for selected in state('selected_files'):
            if selected in [".",".."]:
                logger.warning(f"Skipping selected file: {selected}")
                continue

            # Not skipped...get to work!
            count += 1
            line_open_and_close(selected, prefix)
    

    # All done, return mode to 'select'        
    with page:
        st.session_state.mode = 'select'
        clear_selected_files( )
        st.success(f"Processing completed for {count} files!")



# MAIN ---------------------------------------------------------

if __name__ == '__main__':

    # Initialize the session_state
    if not state('mode'):
        st.session_state.mode = 'select'
    if not state('logger'):
        logger.add("app.log", rotation="500 MB")
        logger.info('This is add-template-tracking/app.py!')
        st.session_state.logger = logger
    if not state('selected_files'):
        st.session_state.selected_files = ["."]   # must be initialized to a non-empty array!
    if not state('file_regex'):
        st.session_state.file_regex = False
    if not state('show_hidden'):
        st.session_state.show_hidden = True

    if not state('tag_prefix'):
        st.session_state.tag_prefix = 'cb:'
    if not state('remove_path_levels'):
        st.session_state.remove_path_levels = 4

    # Add a sidebar for control and display.
    with st.sidebar:

        # Prep for number of selected files
        selected = state('selected_files')
        count = len(selected) - 1

        # Show hidden...
        st.session_state['show_hidden'] = st.checkbox(f"Show hidden directories and files", value=True)

        # File type regex...
        if not count:
            st.session_state['file_regex'] = st.text_input(f"Specify ONE file type/extension to limit your list of selectable files.", help=f"For example, '.html' to list only files with an 'html' extension.", value="")
            r = state('file_regex')
            if r and not r.startswith('.'):
                st.session_state['file_regex'] = '.' + r    
        elif not state('file_regex'):
            st.warning(f"You have specified NO file type/extension to limit your list of selectable files.\n\nThis setting cannot be changed since you have one or more files selected for processing.")
        else:
            st.warning(f"You have specified a file type/extension of '**{state('file_regex')}**' to limit your list of selectable files.\n\nThis setting cannot be changed since you have one or more files selected for processing.")

        # Number of selected files
        # plural logic from https://stackoverflow.com/questions/21872366/plural-string-formatting
        if count:
            st.success(f"You have {count} file{'s'[:count^1]} selected for processing.")  
        else:
            st.warning(f"You have NO files selected for processing")

        # Clear selected files...
        if count:
            st.button(f"Clear Selected File List", help=f"Click here to clear your selected file list.", on_click=clear_selected_files)

        # Tag prefix text (default is 'cb:')
        st.session_state['tag_prefix'] = st.text_input(f"Prefix to apply inside tags", value='cb:')   

        # Number of subdir levels to remove from paths (default is 4)
        st.session_state['remove_path_levels'] = st.number_input(f"Number of prefix subdirs to remove for relative paths", min_value=0, value=4)   

        if count > 0:
            st.button(f"Go for Processing {count} File{'s'[:count^1]}!", help=f"Click here once all files have been selected for processing.", on_click=go_for_processing)


    with st.container(key='main-container'):

        st.session_state["my_path"] = update_new_path( )

        if state("run_again"):
            st.session_state["run_again"] = False
            update_paths( )
            state("my_path")
            st.rerun( )

        state("my_path")
