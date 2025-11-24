#!/usr/bin/env python3
import zlib
import curses

def calculate_series_crc(ds):
    """
    Calculate CRC32 checksum for a DICOM series similar to dcm2niix.
    dcm2niix calculates CRC from the SeriesInstanceUID string.
    """
    if hasattr(ds, 'SeriesInstanceUID'):
        series_uid = str(ds.SeriesInstanceUID)
        # Calculate CRC32 and ensure it's a positive 32-bit integer
        crc = zlib.crc32(series_uid.encode('utf-8')) & 0xFFFFFFFF
        return crc
    return 0

def interactive_menu(stdscr, sorted_acquisitions):
    """
    Interactive menu using arrow keys to select a series.
    Returns the selected series number.
    """
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
    # Build a flat list of series with their info
    menu_items = []
    for acq_num, series_list in sorted_acquisitions:
        # Add acquisition header
        if acq_num is not None:
            menu_items.append(('header', f"Acquisition {acq_num}:", None, None))
        else:
            menu_items.append(('header', "No Acquisition Number:", None, None))
        
        # Sort series within acquisition by Series Number
        sorted_series = sorted(series_list, key=lambda x: x[1][0][1].SeriesNumber)
        
        for series_uid, files in sorted_series:
            first_ds = files[0][1]
            series_number = getattr(first_ds, 'SeriesNumber', 'N/A')
            series_description = getattr(first_ds, 'SeriesDescription', 'N/A')
            sequence_name = getattr(first_ds, 'SequenceName', None)
            protocol_name = getattr(first_ds, 'ProtocolName', None)
            
            # Build the sequence/protocol info in parentheses
            seq_protocol_info = []
            if sequence_name:
                seq_protocol_info.append(sequence_name)
            if protocol_name:
                seq_protocol_info.append(protocol_name)
            
            if seq_protocol_info:
                additional_info = f" ({', '.join(seq_protocol_info)})"
            else:
                additional_info = ""
            
            display_text = f"  Series {series_number}: {series_description}{additional_info}"
            menu_items.append(('series', display_text, series_number, (series_uid, files)))
    
    current_row = 0
    # Find first selectable item
    while current_row < len(menu_items) and menu_items[current_row][0] == 'header':
        current_row += 1
    
    top_line = 0
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        stdscr.addstr(0, 0, "Available DICOM Series (Use ↑/↓ arrows, Enter to select, r to refresh, q to quit)", curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * min(w-1, 80))
        
        # Calculate visible range
        visible_lines = h - 3
        if current_row < top_line:
            top_line = current_row
        elif current_row >= top_line + visible_lines:
            top_line = current_row - visible_lines + 1
        
        # Display menu items
        for idx in range(top_line, min(top_line + visible_lines, len(menu_items))):
            y = idx - top_line + 2
            if y >= h:
                break
                
            item_type, text, series_num, data = menu_items[idx]
            
            if item_type == 'header':
                stdscr.addstr(y, 0, text[:w-1], curses.A_BOLD)
            else:
                if idx == current_row:
                    stdscr.addstr(y, 0, text[:w-1], curses.A_REVERSE)
                else:
                    stdscr.addstr(y, 0, text[:w-1])
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            # Move up to previous selectable item
            new_row = current_row - 1
            while new_row >= 0 and menu_items[new_row][0] == 'header':
                new_row -= 1
            if new_row >= 0:
                current_row = new_row
        elif key == curses.KEY_DOWN:
            # Move down to next selectable item
            new_row = current_row + 1
            while new_row < len(menu_items) and menu_items[new_row][0] == 'header':
                new_row += 1
            if new_row < len(menu_items):
                current_row = new_row
        elif key == ord('\n') or key == curses.KEY_ENTER:
            # Select current item
            if menu_items[current_row][0] == 'series':
                return menu_items[current_row][2], menu_items[current_row][3]
        elif key == ord('r') or key == ord('R'):
            # Signal to refresh
            return 'refresh', None
        elif key == ord('q') or key == ord('Q'):
            return None, None

def dicom_series_selector(dicom_dir, menu_type='simple'):
    """
    Select a DICOM series from a given DICOM export directory.

    Parameters:
    dicom_dir (str): Path to the directory containing DICOM files.
    menu_type (str): Type of menu to display for selection. Default is 'simple'.

    Returns:
    for now, only prints a number of information about the selected series.
    (e.g. series number, series CRC, number of files, name of first file, etc.)
    """
    import os
    import pydicom
    from pydicom.errors import InvalidDicomError
    from collections import defaultdict

    while True:  # Main loop to allow refreshing
        # Gather all DICOM files in the directory
        dicom_files = []
        for root, _, files in os.walk(dicom_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                    dicom_files.append((file_path, ds))
                except InvalidDicomError:
                    continue

        # Group files by Series Instance UID
        series_dict = defaultdict(list)
        for file_path, ds in dicom_files:
            series_uid = ds.SeriesInstanceUID
            series_dict[series_uid].append((file_path, ds))

        # Group series by AcquisitionNumber
        acquisition_groups = defaultdict(list)
        for series_uid, files in series_dict.items():
            first_ds = files[0][1]
            acquisition_number = getattr(first_ds, 'AcquisitionNumber', None)
            acquisition_groups[acquisition_number].append((series_uid, files))
        
        # Sort acquisitions and series within each acquisition
        sorted_acquisitions = sorted(acquisition_groups.items(), key=lambda x: (x[0] is None, x[0]))
        
        # Build a dictionary mapping series number to (series_uid, files)
        series_number_map = {}
        for acq_num, series_list in sorted_acquisitions:
            for series_uid, files in series_list:
                first_ds = files[0][1]
                series_number = getattr(first_ds, 'SeriesNumber', None)
                if series_number is not None:
                    series_number_map[series_number] = (series_uid, files)
        
        # Choose menu type
        if menu_type == 'interactive':
            # Use curses for interactive selection
            try:
                selected_series_num, selected_data = curses.wrapper(interactive_menu, sorted_acquisitions)
                if selected_series_num == 'refresh':
                    continue  # Restart the loop to rescan
                if selected_series_num is None:
                    print("Selection cancelled")
                    return
                selected_series_uid, selected_files = selected_data
                break  # Exit the loop after successful selection
            except Exception as e:
                print(f"Error in interactive mode: {e}")
                print("Falling back to simple mode...")
                menu_type = 'simple'
        
        if menu_type == 'simple':
            # Display available series grouped by acquisition
            print("Available DICOM Series:")
            for acq_num, series_list in sorted_acquisitions:
                if acq_num is not None:
                    print(f"\nAcquisition {acq_num}:")
                else:
                    print(f"\nNo Acquisition Number:")
                
                # Sort series within acquisition by Series Number
                sorted_series = sorted(series_list, key=lambda x: x[1][0][1].SeriesNumber)
                
                for series_uid, files in sorted_series:
                    first_ds = files[0][1]
                    series_number = getattr(first_ds, 'SeriesNumber', 'N/A')
                    series_description = getattr(first_ds, 'SeriesDescription', 'N/A')
                    sequence_name = getattr(first_ds, 'SequenceName', None)
                    protocol_name = getattr(first_ds, 'ProtocolName', None)
                    
                    # Build the sequence/protocol info in parentheses
                    seq_protocol_info = []
                    if sequence_name:
                        seq_protocol_info.append(sequence_name)
                    if protocol_name:
                        seq_protocol_info.append(protocol_name)
                    
                    if seq_protocol_info:
                        additional_info = f" ({', '.join(seq_protocol_info)})"
                    else:
                        additional_info = ""
                    
                    print(f"  Series {series_number}: {series_description}{additional_info}")

            # User selects a series by series number
            selection = input("\nSelect a series by series number (or 'r' to refresh, 'q' to quit): ")
            
            if selection.lower() == 'r':
                continue  # Restart the loop to rescan
            elif selection.lower() == 'q':
                print("Selection cancelled")
                return
            
            try:
                selection = int(selection)
            except ValueError:
                print(f"Error: Invalid input")
                return
            
            if selection not in series_number_map:
                print(f"Error: Series number {selection} not found")
                return
            
            selected_series_uid, selected_files = series_number_map[selection]
            break  # Exit the loop after successful selection

    # Print information about the selected series
    # Sort files alphabetically by path and get the first one
    sorted_files = sorted(selected_files, key=lambda x: x[0])
    first_file_path, first_ds = sorted_files[0]
    series_crc = calculate_series_crc(first_ds)
    print(f"\nSelected Series UID: {selected_series_uid}")
    print(f"Series Number: {first_ds.SeriesNumber}")
    print(f"Series CRC: {series_crc}")
    print(f"Number of Files: {len(selected_files)}")
    print(f"First File Path: {first_file_path}")
    return series_crc



def test():
    dicom_dir = 'realtime_export/20251120.sfassnacht_phantom_discard.25.11.20_14_26_40_STD_1.3.12.2.1107.5.2.0.18951'
    # Use menu_type='interactive' for arrow key selection, or 'simple' for number input
    dicom_series_selector(dicom_dir, menu_type='interactive')

if __name__ == "__main__":
    test()
