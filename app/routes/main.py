from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, abort, send_file
from app.models.database import db, FGasRecord
from datetime import datetime
import re
import os
import mimetypes
from werkzeug.utils import secure_filename as werkzeug_secure_filename
# import humanize  # Comment out since we'll use our own function
from pathlib import Path
from markupsafe import Markup
import unicodedata
from flask_login import login_required, current_user
from app.routes.auth import admin_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

# Define a function to format file sizes
def format_file_size(size_bytes):
    """Format file size in a human-readable way."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

bp = Blueprint('main', __name__)

# Custom filter to add line breaks after periods
@bp.app_template_filter('format_text')
def format_text_filter(text):
    if not text:
        return ""
    
    # First, preserve any existing newline characters
    result = text
    
    # Replace all period+space with period+newline
    result = result.replace('. ', '.\n')
    
    # Also handle period at the end
    if result.endswith('.'):
        result += '\n'
    
    # Replace other common sentence endings with line breaks
    result = result.replace('! ', '!\n')
    result = result.replace('? ', '?\n')
    
    # Handle line breaks in the input text
    result = result.replace('\r\n', '\n')  # Normalize Windows-style newlines
    
    # Ensure all newlines are preserved when rendering in HTML
    result = result.replace('\n', '<br>')
    
    return Markup(result)  # Mark as safe HTML

@bp.route('/', methods=['GET'])
def index():
    records = FGasRecord.get_all_records()
    return render_template('index.html', records=records)

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        id = request.form['id']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        comments = request.form['comments']
        filled_kg = float(request.form['filled_kg'])
        
        # Check if ID+date already exists
        existing_record = FGasRecord.get_record_by_id_and_date(id, date)
        if existing_record:
            flash(f'A record with ID {id} on date {date} already exists!', 'error')
            return redirect(url_for('main.register'))
        
        # Create new record
        new_record = FGasRecord(id=id, date=date, comments=comments, filled_kg=filled_kg)
        
        # Add to database
        db.session.add(new_record)
        db.session.commit()
        
        flash('Record added successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('register.html')

@bp.route('/results', methods=['GET'])
def results():
    search_id = request.args.get('search_id', '')
    
    if search_id:
        # If search_id is provided, filter by ID
        records = FGasRecord.get_record_by_id(search_id)
    else:
        # Otherwise, get all records
        records = FGasRecord.get_all_records()
    
    return render_template('results.html', records=records, search_id=search_id)

@bp.route('/search', methods=['POST'])
def search():
    search_id = request.form.get('search_id', '')
    return redirect(url_for('main.results', search_id=search_id))

@bp.route('/record/<id>/<date>', methods=['GET'])
def view_record(id, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        record = FGasRecord.get_record_by_id_and_date(id, date_obj)
        if not record:
            flash('Record not found!', 'error')
            return redirect(url_for('main.results'))
        
        # Return a single record view
        return render_template('record.html', record=record)
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('main.results'))

@bp.route('/delete_record/<id>/<date>', methods=['POST'])
@login_required
def delete_record(id, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        record = FGasRecord.get_record_by_id_and_date(id, date_obj)
        
        if not record:
            flash('Record not found!', 'error')
            return redirect(url_for('main.results'))
        
        # Delete the record
        db.session.delete(record)
        db.session.commit()
        
        flash(f'Record with ID {id} on date {date} was deleted successfully!', 'success')
        return redirect(url_for('main.index'))
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('main.results'))
    except Exception as e:
        flash(f'Error deleting record: {str(e)}', 'error')
        return redirect(url_for('main.results'))

@bp.route('/documents/', defaults={'folder_path': ''}, methods=['GET'])
@bp.route('/documents/<path:folder_path>', methods=['GET'])
def documents(folder_path):
    """
    Display documents and folders in the specified path.
    """
    # Path to doc folder
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    
    # Construct the full path
    if folder_path:
        full_path = os.path.join(base_path, folder_path)
    else:
        full_path = base_path
    
    # Check if the path exists
    if not os.path.exists(full_path):
        flash('The requested folder does not exist.', 'error')
        return redirect(url_for('main.documents'))
    
    # Check if it's a directory
    if not os.path.isdir(full_path):
        flash('The requested path is not a folder.', 'error')
        return redirect(url_for('main.documents'))
    
    # Create breadcrumbs for navigation
    breadcrumbs = []
    if folder_path:
        parts = folder_path.split('/')
        current_path = ""
        
        # Add root
        breadcrumbs.append({"name": "Root", "path": ""})
        
        # Add each part of the path
        for i, part in enumerate(parts):
            if current_path:
                current_path += f"/{part}"
            else:
                current_path = part
            
            breadcrumbs.append({
                "name": part,
                "path": current_path
            })
    
    # Get folders and files
    folders = []
    files = []
    
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        
        if os.path.isdir(item_path):
            # Count items in the folder
            item_count = len(os.listdir(item_path))
            
            folders.append({
                "name": item,
                "path": os.path.join(folder_path, item) if folder_path else item,
                "files": os.listdir(item_path)
            })
        else:
            # Get file stats
            stats = os.stat(item_path)
            
            # Format the size
            size = format_file_size(stats.st_size)
            
            # Format the modified date
            modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
            
            # Get file type
            file_type, _ = mimetypes.guess_type(item_path)
            if file_type:
                file_type = file_type.split('/')[1].upper()
            else:
                file_type = "UNKNOWN"
                
            files.append({
                "name": item,
                "path": os.path.join(folder_path, item) if folder_path else item,
                "size": size,
                "modified": modified,
                "type": file_type
            })
    
    # Sort folders and documents alphabetically
    folders.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())
    
    return render_template(
        'documents.html', 
        folders=folders, 
        files=files, 
        folder_path=folder_path,
        breadcrumbs=breadcrumbs
    )

@bp.route('/view/<path:file_path>')
def view_file(file_path):
    """Serve a file for viewing in the browser"""
    # Path to doc folder
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    
    # Split the path into directory and filename
    dir_path, filename = os.path.split(file_path)
    file_dir = os.path.join(base_doc_folder, dir_path) if dir_path else base_doc_folder
    
    # Serve the file for viewing in the browser
    return send_from_directory(file_dir, filename)

@bp.route('/download/<path:file_path>')
def download_file(file_path):
    """Download a file"""
    # Path to doc folder
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    
    # Split the path into directory and filename
    dir_path, filename = os.path.split(file_path)
    file_dir = os.path.join(base_doc_folder, dir_path) if dir_path else base_doc_folder
    
    # Serve the file as an attachment (for download)
    return send_from_directory(file_dir, filename, as_attachment=True)

@bp.route('/upload', defaults={'folder_path': ''}, methods=['GET', 'POST'])
@bp.route('/upload/<path:folder_path>', methods=['GET', 'POST'])
def upload_file(folder_path):
    """Upload a file to the specified folder"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('main.upload_file', folder_path=folder_path))
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('main.upload_file', folder_path=folder_path))
        
        # Check if a destination folder was selected
        selected_folder = request.form.get('folder_path', '')
        destination_folder = selected_folder if selected_folder else folder_path
        
        if file:
            # Use our custom secure_filename instead of werkzeug's version
            filename = secure_filename(file.filename)
            
            # Path to doc folder
            base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
            
            # Get the upload folder
            upload_folder = os.path.join(base_doc_folder, destination_folder)
            
            # Create directory if it doesn't exist
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save the file
            file.save(os.path.join(upload_folder, filename))
            
            flash(f'File {filename} uploaded successfully', 'success')
            return redirect(url_for('main.documents', folder_path=destination_folder))
    
    # Create breadcrumbs for navigation
    breadcrumbs = []
    if folder_path:
        parts = folder_path.split('/')
        current_path = ""
        
        # Add root
        breadcrumbs.append({"name": "Root", "path": ""})
        
        # Add each part of the path
        for i, part in enumerate(parts):
            if current_path:
                current_path += f"/{part}"
            else:
                current_path = part
            
            breadcrumbs.append({
                "name": part,
                "path": current_path
            })
    
    # Get all folders for the dropdown selection
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    folders = []
    
    # Add the root folder
    folders.append({"name": "Root", "path": ""})
    
    # Get all folders in the doc directory (including nested folders)
    for root, dirs, files in os.walk(base_doc_folder):
        for dir_name in dirs:
            # Get the path relative to the base folder
            rel_path = os.path.relpath(os.path.join(root, dir_name), base_doc_folder)
            if rel_path != '.':  # Skip the current directory entry
                # Create a more readable display name
                display_name = rel_path.replace('\\', '/').replace('/', ' > ')
                folders.append({
                    "name": display_name,
                    "path": rel_path
                })
    
    # Sort folders by name
    folders.sort(key=lambda x: x["name"].lower())
    
    # Ensure folder_path is a string to avoid comparison issues
    if folder_path is None:
        folder_path = ""
    
    # Normalize paths for proper comparison
    folder_path = folder_path.replace('\\', '/')
    for folder in folders:
        folder['path'] = folder['path'].replace('\\', '/')
    
    return render_template('upload.html', folder_path=folder_path, breadcrumbs=breadcrumbs, folders=folders)

@bp.route('/delete_by_name/<filename>', methods=['GET', 'POST'])
def delete_by_name(filename):
    """Delete a file by its name (search in all directories)"""
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    found = False
    
    # Check for Norwegian characters
    has_norwegian = 'ø' in filename or 'æ' in filename or 'å' in filename or 'Ø' in filename or 'Æ' in filename or 'Å' in filename
    
    try:
        # Search for the file in all directories
        for root, dirs, files in os.walk(base_doc_folder):
            # Try exact match
            if filename in files:
                file_path = os.path.join(root, filename)
                os.remove(file_path)
                rel_dir = os.path.relpath(root, base_doc_folder)
                rel_dir = '' if rel_dir == '.' else rel_dir
                flash(f'File "{filename}" deleted successfully from {rel_dir}', 'success')
                found = True
                return redirect(url_for('main.documents', folder_path=rel_dir))
            
            # If we have Norwegian characters, try case-insensitive and normalized matches
            if has_norwegian and not found:
                for file in files:
                    # Case-insensitive compare
                    if file.lower() == filename.lower():
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        rel_dir = os.path.relpath(root, base_doc_folder)
                        rel_dir = '' if rel_dir == '.' else rel_dir
                        flash(f'File "{file}" deleted successfully from {rel_dir}', 'success')
                        found = True
                        return redirect(url_for('main.documents', folder_path=rel_dir))
                    
                    # Try a more forgiving comparison for Norwegian characters
                    normalized_file = normalize_norwegian(file)
                    normalized_filename = normalize_norwegian(filename)
                    
                    if normalized_file == normalized_filename:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        rel_dir = os.path.relpath(root, base_doc_folder)
                        rel_dir = '' if rel_dir == '.' else rel_dir
                        flash(f'File "{file}" deleted successfully from {rel_dir}', 'success')
                        found = True
                        return redirect(url_for('main.documents', folder_path=rel_dir))
        
        if not found:
            flash(f'File "{filename}" not found.', 'error')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('main.documents'))

@bp.route('/delete/<path:file_path>', methods=['POST'])
def delete_file(file_path):
    """Delete a file"""
    # Path to doc folder
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    
    # Check if a basename was provided in the form
    file_basename = request.form.get('file_basename')
    if file_basename:
        print(f"Using provided basename: {file_basename}")
        # Always use the basename from the form if available, as it's more reliable
        original_filename = file_basename
    else:
        # Extract JUST the basename from the file_path, no matter how nested
        original_filename = os.path.basename(file_path)
    
    # Check for URL-encoded characters in filename and decode them
    try:
        from urllib.parse import unquote
        decoded_filename = unquote(original_filename)
        if decoded_filename != original_filename:
            print(f"Decoded URL-encoded characters: {decoded_filename}")
            original_filename = decoded_filename
    except Exception as e:
        print(f"Error decoding URL: {str(e)}")
    
    # Check if we should auto-correct the filename
    auto_correct = request.args.get('auto_correct', 'true').lower() in ('true', '1', 'yes')
    
    # IMPORTANT: Clean the filename to ensure no folder prefixes
    # This is to prevent issues where folder names get prefixed to the filename
    # E.g., "divmartini.jpg" where "div" is a folder name
    pure_filename = original_filename
    
    # For debugging
    print(f"Original filename: {original_filename}")
    
    # List all files in the doc directory to help debug
    print("All files in doc directory:")
    all_files = []
    for root, dirs, files in os.walk(base_doc_folder):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), base_doc_folder)
            all_files.append((file, rel_path, os.path.join(root, file)))
            print(f"  - {file} ({rel_path})")
    
    # Try to normalize the filename first
    temp_filename = original_filename.strip()
    
    # Handle specific known problematic files
    if "f-gasHVAC_type_72_Teste_instruks_1.ppt" in temp_filename:
        pure_filename = "HVAC_type_72_Teste_instruks_1.ppt"
        print(f"Fixed f-gas prefix case: {pure_filename}")
    elif "kupe_docTEST_AV_VARMEOVNER.ppt" in temp_filename:
        pure_filename = "TEST_AV_VARMEOVNER.ppt"
        print(f"Fixed kupe_doc prefix case: {pure_filename}")
    # Special handling for tik-tok_3046121.png in all its variants
    elif "ik-tok_3046121" in temp_filename or "tik-tok_3046121" in temp_filename:
        pure_filename = "tik-tok_3046121.png"
        print(f"Applied comprehensive fix for tik-tok file: {pure_filename}")
    # Exact case handling for reported issues
    elif original_filename == "div tik-tok_3046121.png":
        pure_filename = "tik-tok_3046121.png"
        print(f"Fixed specific case: {pure_filename}")
    elif original_filename == " ik-tok_3046121.png":
        pure_filename = "tik-tok_3046121.png"
        print(f"Fixed missing 't' case: {pure_filename}")
    
    # Check for more specific folder-as-prefix issues
    known_folders = ["f-gas", "f-Gas", "F-gas", "F-Gas", "kupe_doc", "kupe_", "div", 
                      "test", "img", "images", "docs", "files"]
    for prefix in known_folders:
        if temp_filename.lower().startswith(prefix.lower()) and len(temp_filename) > len(prefix):
            potential_name = temp_filename[len(prefix):]
            print(f"Found folder prefix '{prefix}': Potential name = {potential_name}")
            pure_filename = potential_name
            break
    
    # Get all folder names to detect potential prefixes
    all_folder_names = set()
    for root, dirs, _ in os.walk(base_doc_folder):
        for dir_name in dirs:
            all_folder_names.add(dir_name.lower())
            # Also add variations with common separators
            all_folder_names.add(f"{dir_name.lower()}_")
            all_folder_names.add(f"{dir_name.lower()}-")
            
    print(f"All possible folder prefixes: {all_folder_names}")
    
    # Check if the filename starts with any folder name
    filename_lower = temp_filename.lower()
    for folder_name in all_folder_names:
        if filename_lower.startswith(folder_name):
            potential_name = temp_filename[len(folder_name):]
            print(f"Found exact folder prefix '{folder_name}': Potential name = {potential_name}")
            
            # Check if the potential name exists in the file list
            if all_files:
                for file_info in all_files:
                    if file_info[0].lower() == potential_name.lower():
                        print(f"Found exact match for {potential_name} in file list after removing folder prefix")
                        pure_filename = potential_name
                        break
    
    # Check if we have control characters or unusual symbols
    has_control_chars = False
    for char in pure_filename:
        if char < ' ' or ord(char) > 126:  # ASCII control chars or non-ASCII characters
            if char not in "øæåØÆÅ":  # Except Norwegian characters
                has_control_chars = True
                break
    
    if has_control_chars:
        print(f"Detected control characters or special symbols in: {pure_filename}")
        # Create a version with only alphanumeric and essential punctuation
        clean_filename = ""
        for char in pure_filename:
            if char.isalnum() or char in "._- " or char in "øæåØÆÅ":
                clean_filename += char
        
        print(f"Cleaned version: {clean_filename}")
        
        # Try to find a match with the cleaned version
        for file_info in all_files:
            # Create a similarly cleaned version of the file for comparison
            clean_file = ""
            for char in file_info[0]:
                if char.isalnum() or char in "._- " or char in "øæåØÆÅ":
                    clean_file += char
            
            # Compare the cleaned versions
            if clean_file.lower() == clean_filename.lower():
                pure_filename = file_info[0]
                print(f"Found match after cleaning special chars: {pure_filename}")
                break
            
            # Also try a simple comparison where we strip out all non-alphanumeric
            if ''.join(c for c in clean_file.lower() if c.isalnum()) == ''.join(c for c in clean_filename.lower() if c.isalnum()):
                pure_filename = file_info[0]
                print(f"Found match using alphanumeric-only comparison: {pure_filename}")
                break
    
    # Special handling for Norwegian characters
    if 'ø' in pure_filename or 'æ' in pure_filename or 'å' in pure_filename or 'Ø' in pure_filename or 'Æ' in pure_filename or 'Å' in pure_filename:
        print(f"File with Norwegian characters detected: {pure_filename}")
        # Try to find the file directly in all files - case insensitive compare
        norwegian_found = False
        for file_info in all_files:
            # Case-insensitive compare
            if file_info[0].lower() == pure_filename.lower():
                # Use the exact filename from the file system for accuracy
                pure_filename = file_info[0]
                print(f"Found exact Norwegian filename match: {pure_filename}")
                norwegian_found = True
                break
        
        if not norwegian_found:
            # Try a more forgiving comparison for Norwegian characters
            for file_info in all_files:
                # Replace Norwegian characters for comparison purposes
                normalized_file = normalize_norwegian(file_info[0])
                normalized_pure = normalize_norwegian(pure_filename)
                
                if normalized_file == normalized_pure:
                    # Use the exact filename from the file system
                    pure_filename = file_info[0]  
                    print(f"Found fuzzy Norwegian filename match: {pure_filename}")
                    break
    
    # General solution for any folder name prefix
    if "_" in temp_filename or "-" in temp_filename:
        parts = re.split(r'[_-]', temp_filename, 1)  # Split on first _ or -
        if len(parts) > 1 and len(parts[0]) > 0:
            potential_folder_prefix = parts[0]
            potential_real_filename = temp_filename[len(potential_folder_prefix):]
            
            # Check if the potential filename starts with _ or -
            if potential_real_filename.startswith("_") or potential_real_filename.startswith("-"):
                potential_real_filename = potential_real_filename[1:]  # Remove the separator
            
            print(f"Potential folder prefix: '{potential_folder_prefix}', Remaining: '{potential_real_filename}'")
            
            # If we have a list of all files, check if the remaining part exists
            if all_files:
                for file_info in all_files:
                    if file_info[0].lower() == potential_real_filename.lower():
                        print(f"Found match for {potential_real_filename} in file list")
                        pure_filename = potential_real_filename
                        break
    
    # Additional handling for variations in search
    # Convert common misspelled variants to the correct filename for search
    if original_filename.strip() == "ik-tok_3046121.png" or original_filename.strip() == " ik-tok_3046121.png":
        # For searching purposes, ensure we're looking for the correct file
        file_path = file_path.replace(original_filename, "tik-tok_3046121.png")
        print(f"Modified file_path for search: {file_path}")
        
        # Also add to the list of files to search for
        if all_files:
            all_files.append(("tik-tok_3046121.png", "tik-tok_3046121.png", os.path.join(base_doc_folder, "tik-tok_3046121.png")))
            print("Added tik-tok_3046121.png to search list")
    
    # Special search for this specific file - search for it directly
    if "tik-tok_3046121.png" in pure_filename or "ik-tok_3046121" in pure_filename:
        found_tiktok = False
        print("Doing direct search for tik-tok file...")
        for root, dirs, files in os.walk(base_doc_folder):
            # Look for any variant
            tiktok_variants = ["tik-tok_3046121.png", "ik-tok_3046121.png", " ik-tok_3046121.png", "tik-tok_3046121"]
            for variant in tiktok_variants:
                if variant in files:
                    # Found it - delete directly
                    full_file = os.path.join(root, variant)
                    print(f"Found tik-tok file variant: {variant} at {full_file}")
                    try:
                        os.remove(full_file)
                        rel_dir = os.path.relpath(root, base_doc_folder)
                        rel_dir = '' if rel_dir == '.' else rel_dir
                        flash(f'File "{pure_filename}" deleted successfully (variant {variant})', 'success')
                        found_tiktok = True
                        return redirect(url_for('main.documents', folder_path=rel_dir))
                    except Exception as e:
                        print(f"Error deleting tik-tok file variant: {str(e)}")
    
    # Check for common folder prefixes that might be incorrectly prepended
    common_prefixes = ["div", "test", "img", "images", "docs", "files"]
    for prefix in common_prefixes:
        # Look for prefix followed by either nothing, space, dash, or underscore
        if pure_filename.lower().startswith(prefix.lower()):
            print(f"Found prefix: {prefix} in {pure_filename}")
            
            # Case 1: prefix followed by space
            if len(pure_filename) > len(prefix) and pure_filename[len(prefix)] == ' ':
                potential_name = pure_filename[len(prefix)+1:]  # Skip prefix and space
                print(f"Trying potential name (space case): {potential_name}")
                pure_filename = potential_name
                break
                
            # Case 2: prefix directly attached to rest
            else:
                potential_name = pure_filename[len(prefix):]
                print(f"Trying potential name (no space): {potential_name}")
                if potential_name.startswith(('-', '_')):
                    potential_name = potential_name[1:]
                    print(f"After removing separator: {potential_name}")
                pure_filename = potential_name
                break
                
    print(f"Final cleaned filename: {pure_filename}")
    
    # Try with unquoted filename (for spaces and special chars)
    try:
        from urllib.parse import unquote
        unquoted_filename = unquote(pure_filename)
        print(f"  - Unquoted filename: {unquoted_filename}")
    except:
        unquoted_filename = pure_filename
    
    # Full path to the file
    file_full_path = os.path.join(base_doc_folder, file_path)
    
    # Get the folder path to redirect back to
    folder_path = os.path.dirname(file_path)
    
    # Debug the paths
    print(f"Trying to delete file: {file_path}")
    print(f"Full path: {file_full_path}")
    print(f"Base doc folder: {base_doc_folder}")
    print(f"Folder path: {folder_path}")
    
    # Try multiple approaches to find and delete the file
    try:
        found = False
        
        # First try: direct path
        if os.path.exists(file_full_path) and os.path.isfile(file_full_path):
            os.remove(file_full_path)
            flash(f'File "{pure_filename}" deleted successfully', 'success')
            found = True
        
        # Second try: unquoted path
        elif unquoted_filename != pure_filename:
            unquoted_path = os.path.join(base_doc_folder, folder_path, unquoted_filename)
            if os.path.exists(unquoted_path) and os.path.isfile(unquoted_path):
                os.remove(unquoted_path)
                flash(f'File "{unquoted_filename}" deleted successfully', 'success')
                found = True
        
        # Third try: search by exact filename
        if not found:
            print(f"Searching for file with name: {pure_filename}")
            
            # Check for Norwegian characters
            has_norwegian = 'ø' in pure_filename or 'æ' in pure_filename or 'å' in pure_filename or 'Ø' in pure_filename or 'Æ' in pure_filename or 'Å' in pure_filename
            
            for root, dirs, files in os.walk(base_doc_folder):
                # Try exact match with the pure filename
                if pure_filename in files:
                    full_file = os.path.join(root, pure_filename)
                    os.remove(full_file)
                    rel_dir = os.path.relpath(root, base_doc_folder)
                    rel_dir = '' if rel_dir == '.' else rel_dir
                    flash(f'File "{pure_filename}" deleted successfully', 'success')
                    found = True
                    return redirect(url_for('main.documents', folder_path=rel_dir))
                
                # Try with unquoted basename
                if unquoted_filename in files:
                    full_file = os.path.join(root, unquoted_filename)
                    os.remove(full_file)
                    rel_dir = os.path.relpath(root, base_doc_folder)
                    rel_dir = '' if rel_dir == '.' else rel_dir
                    flash(f'File "{unquoted_filename}" deleted successfully', 'success')
                    found = True
                    return redirect(url_for('main.documents', folder_path=rel_dir))
                
                # Special case for Norwegian characters - case insensitive comparison
                if has_norwegian:
                    for file in files:
                        # Case-insensitive compare
                        if file.lower() == pure_filename.lower():
                            full_file = os.path.join(root, file)
                            os.remove(full_file)
                            rel_dir = os.path.relpath(root, base_doc_folder)
                            rel_dir = '' if rel_dir == '.' else rel_dir
                            flash(f'File "{file}" deleted successfully', 'success')
                            found = True
                            return redirect(url_for('main.documents', folder_path=rel_dir))
                        
                        # Try more advanced Norwegian character matching
                        if could_be_norwegian_equivalent(file, pure_filename):
                            full_file = os.path.join(root, file)
                            os.remove(full_file)
                            rel_dir = os.path.relpath(root, base_doc_folder)
                            rel_dir = '' if rel_dir == '.' else rel_dir
                            flash(f'File "{file}" deleted successfully using Norwegian character matching', 'success')
                            found = True
                            return redirect(url_for('main.documents', folder_path=rel_dir))
        
        if not found and auto_correct:
            # Find the most similar file and auto-correct
            similar_files = []
            
            # Try to clean the filename by removing common folder prefixes
            clean_filename = pure_filename
            for prefix in common_prefixes:
                if clean_filename.lower().startswith(prefix) and not clean_filename.lower() == prefix:
                    # Try removing the prefix and any separator
                    potential_name = clean_filename[len(prefix):]
                    if potential_name.startswith("-") or potential_name.startswith("_"):
                        potential_name = potential_name[1:]
                    
                    # Test if this improves matches
                    for file, _, _ in all_files:
                        if file.lower() == potential_name.lower():
                            clean_filename = potential_name
                            break
            
            # Calculate similarity for each file (using ONLY filenames, not paths)
            for filename, rel_path, full_path in all_files:
                # Skip folders
                if os.path.isdir(full_path):
                    continue
                    
                # Simple similarity check between pure filenames
                target = pure_filename.lower()  # Use the pure filename extracted at the start
                clean_target = clean_filename.lower()  # Try the cleaned version too
                current = filename.lower()  # This is already just the filename
                
                # Debug similarity check
                print(f"Comparing: '{target}' with '{current}'")
                
                # Check multiple versions of the target
                similarity_versions = [
                    (target, "original"),
                    (clean_target, "cleaned")
                ]
                
                # Add a version with normalized Norwegian characters
                if 'ø' in target or 'æ' in target or 'å' in target or 'Ø' in target or 'Æ' in target or 'Å' in target:
                    normalized_target = normalize_norwegian(target)
                    similarity_versions.append((normalized_target, "norwegian_normalized"))
                
                # Try all versions to find the best similarity
                highest_similarity = 0
                for check_target, version in similarity_versions:
                    # Exact match
                    if current == check_target:
                        similarity = 1.0
                        highest_similarity = max(highest_similarity, similarity)
                        print(f"Exact match with {version}: {similarity}")
                    # Contains relationship
                    elif current in check_target or check_target in current:
                        similarity = 0.7
                        highest_similarity = max(highest_similarity, similarity)
                        print(f"Contains match with {version}: {similarity}")
                    # No spaces match
                    elif current.replace(" ", "") == check_target.replace(" ", ""):
                        similarity = 0.6
                        highest_similarity = max(highest_similarity, similarity)
                        print(f"No spaces match with {version}: {similarity}")
                    # First chars match
                    elif len(current) >= 3 and len(check_target) >= 3 and current[:3] == check_target[:3]:
                        similarity = 0.5
                        highest_similarity = max(highest_similarity, similarity)
                        print(f"First chars match with {version}: {similarity}")
                
                # Use the highest similarity found among all versions
                similarity = highest_similarity
                
                if similarity > 0:
                    print(f"Found similarity {similarity} between '{target}' and '{current}'")
                    parent_dir = os.path.dirname(full_path)
                    rel_dir = os.path.relpath(parent_dir, base_doc_folder)
                    rel_dir = '' if rel_dir == '.' else rel_dir
                    similar_files.append((filename, full_path, rel_dir, similarity))
            
            # Sort by similarity (highest first)
            similar_files.sort(key=lambda x: x[3], reverse=True)
            
            # If we found a similar file, delete it automatically
            if similar_files:
                best_match = similar_files[0]
                best_filename, best_path, best_rel_dir, similarity = best_match
                
                print(f"Best match: {best_filename} with similarity {similarity}")
                print(f"Final filename used in message: {pure_filename}")
                
                if similarity >= 0.5:  # Only auto-correct if reasonably similar
                    os.remove(best_path)
                    
                    # Use the proper display filenames, ensuring no folder prefixes
                    display_original = pure_filename
                    flash(f'File "{display_original}" not found. Automatically deleted similar file "{best_filename}" instead.', 'success')
                    return redirect(url_for('main.documents', folder_path=best_rel_dir))
                else:
                    # Provide a clickable option if similarity is not high enough
                    similar_links = []
                    for name, path, rel_dir, sim in similar_files[:3]:
                        url = url_for('main.delete_by_name', filename=name)
                        similar_links.append(f'<a href="{url}" class="text-primary-600 hover:underline">"{name}"</a>')
                    
                    similar_list = ", ".join(similar_links)
                    message = f'File "{pure_filename}" not found. Did you mean: {similar_list}? <a href="#" class="ml-2 text-xs text-accent-600" onclick="window.history.back()">Cancel</a>'
                    flash(Markup(message), 'error')
            else:
                flash(f'File "{pure_filename}" not found. Check if the filename is correct or try uploading it again.', 'error')
        elif not found:
            # Provide clickable options without auto-correcting
            similar_files = []
            for filename, rel_path, full_path in all_files:
                # Only use the filename without the directory path for comparison
                if (pure_filename.lower() in filename.lower() or 
                    filename.lower() in pure_filename.lower()):
                    similar_files.append((filename, rel_path))
            
            if similar_files:
                similar_links = []
                for name, path in similar_files[:3]:
                    url = url_for('main.delete_by_name', filename=name)
                    similar_links.append(f'<a href="{url}" class="text-primary-600 hover:underline">"{name}"</a>')
                
                similar_list = ", ".join(similar_links)
                message = f'File "{pure_filename}" not found. Did you mean: {similar_list}? <a href="#" class="ml-2 text-xs text-accent-600" onclick="window.history.back()">Cancel</a>'
                flash(Markup(message), 'error')
            else:
                flash(f'File "{pure_filename}" not found. Check if the filename is correct or try uploading it again.', 'error')
    
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('main.documents', folder_path=folder_path))

@bp.route('/create_folder', defaults={'folder_path': ''}, methods=['POST'])
@bp.route('/create_folder/<path:folder_path>', methods=['POST'])
def create_folder(folder_path):
    """Create a new folder"""
    new_folder_name = request.form.get('folder_name', '').strip()
    
    if not new_folder_name:
        flash('Folder name is required', 'error')
        return redirect(url_for('main.documents', folder_path=folder_path))
    
    # Secure the folder name
    new_folder_name = secure_filename(new_folder_name)
    
    # Path to doc folder
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    
    # Get the parent directory
    parent_dir = os.path.join(base_doc_folder, folder_path)
    
    # Create the new folder path
    new_folder_path = os.path.join(parent_dir, new_folder_name)
    
    try:
        if os.path.exists(new_folder_path):
            flash(f'Folder "{new_folder_name}" already exists', 'error')
        else:
            os.makedirs(new_folder_path, exist_ok=True)
            flash(f'Folder "{new_folder_name}" created successfully', 'success')
    except Exception as e:
        flash(f'Error creating folder: {str(e)}', 'error')
    
    return redirect(url_for('main.documents', folder_path=folder_path))

@bp.route('/view_document/<path:file_path>', methods=['GET'])
def view_document(file_path):
    # Path to doc folder
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    
    # Full path to the file
    full_file_path = os.path.join(base_doc_folder, file_path)
    
    # Check if the file exists
    if not os.path.exists(full_file_path) or not os.path.isfile(full_file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.documents'))
    
    # Get file stats
    file_stats = os.stat(full_file_path)
    
    # Get file size in human-readable format
    file_size = file_stats.st_size
    if file_size < 1024:
        size_str = f"{file_size} bytes"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.1f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.1f} MB"
    
    # Get last modified time
    modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    # Get file type
    mime_type, _ = mimetypes.guess_type(full_file_path)
    file_type = "Unknown"
    if mime_type:
        file_type = mime_type
    
    # Check if file is viewable in browser
    is_viewable = True
    is_image = False
    is_pdf = False
    is_text = False
    content = None
    
    if mime_type:
        main_type = mime_type.split('/')[0]
        if main_type == 'image':
            is_image = True
        elif mime_type == 'application/pdf':
            is_pdf = True
        elif main_type == 'text' or mime_type in ['application/json', 'application/xml']:
            is_text = True
            # Read file content for text files (with size limit for safety)
            if file_size < 1024 * 1024:  # 1MB limit for text preview
                try:
                    with open(full_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    is_text = False
                    is_viewable = False
            else:
                is_text = False
                is_viewable = False
    else:
        is_viewable = False
    
    # Create document object
    document = {
        'name': os.path.basename(file_path),
        'path': file_path,
        'type': file_type,
        'size': size_str,
        'modified': modified_time,
        'is_viewable': is_viewable,
        'is_image': is_image,
        'is_pdf': is_pdf,
        'is_text': is_text,
        'content': content
    }
    
    return render_template('view_document.html', document=document)

@bp.route('/serve_file/<path:file_path>', methods=['GET'])
def serve_file(file_path):
    # Path to doc folder
    base_doc_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'doc')
    
    # Split the path into directory and filename
    dir_path, filename = os.path.split(file_path)
    file_dir = os.path.join(base_doc_folder, dir_path) if dir_path else base_doc_folder
    
    # Serve the file for viewing in the browser
    return send_from_directory(file_dir, filename, as_attachment=False)

@bp.route('/record/<id>/<date>/pdf')
def download_pdf(id, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        record = FGasRecord.get_record_by_id_and_date(id, date_obj)
        if not record:
            flash('Record not found!', 'error')
            return redirect(url_for('main.results'))
        
        # Create a BytesIO buffer to store the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        
        # Create the content
        content = []
        
        # Add title
        content.append(Paragraph(f"F-Gas Record Details", title_style))
        content.append(Spacer(1, 20))
        
        # Create the data for the table
        data = [
            ['Field', 'Value'],
            ['ID', record.id],
            ['Date', record.date.strftime('%Y-%m-%d')],
            ['Filled (kg)', f"{record.filled_kg:.2f}"],
            ['Status', record.status or 'N/A'],
            ['Location', record.location or 'N/A']
        ]
        
        # Add created_at and updated_at only if they exist
        if record.created_at:
            data.append(['Created At', record.created_at.strftime('%Y-%m-%d %H:%M')])
        if record.updated_at:
            data.append(['Updated At', record.updated_at.strftime('%Y-%m-%d %H:%M')])
        
        # Create the table
        table = Table(data, colWidths=[150, 350])
        
        # Add table style
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        content.append(table)
        
        # Add comments section with proper formatting
        if record.comments:
            content.append(Spacer(1, 20))
            content.append(Paragraph("Comments:", styles['Heading2']))
            content.append(Spacer(1, 10))
            
            # Format comments with line breaks
            formatted_comments = record.comments.replace('. ', '.\n').replace('! ', '!\n').replace('? ', '?\n')
            if formatted_comments.endswith('.'):
                formatted_comments += '\n'
            
            # Create a custom style for comments with proper line spacing
            comment_style = ParagraphStyle(
                'CommentStyle',
                parent=styles['Normal'],
                spaceAfter=6,
                spaceBefore=6,
                leading=14  # Line spacing
            )
            
            content.append(Paragraph(formatted_comments, comment_style))
        
        # Build the PDF
        doc.build(content)
        
        # Move to the beginning of the BytesIO buffer
        buffer.seek(0)
        
        # Generate filename
        filename = f"fgas_record_{record.id}_{record.date.strftime('%Y%m%d')}.pdf"
        
        # Return the PDF as a downloadable file
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('main.results'))
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('main.results'))

# Helper function to normalize Norwegian characters for comparison
def normalize_norwegian(text):
    """
    Normalize text by replacing Norwegian characters for comparison purposes.
    This is useful when comparing filenames for similarity.
    """
    if not text:
        return ""
    
    # First, remove any control characters and special symbols like ♀ and ♂
    # This uses a whitelist approach for simplicity
    cleaned_text = ""
    for char in text:
        if char.isalnum() or char in "._-" or char in "øæåØÆÅ":
            cleaned_text += char
    
    # If nothing left after cleaning, return the original text lowercase
    if not cleaned_text:
        cleaned_text = text.lower()
    
    # Convert to lowercase and replace Norwegian characters with ASCII equivalents
    return cleaned_text.lower().replace('ø', 'o').replace('æ', 'ae').replace('å', 'a')

# Helper function to check if two strings could be the same with Norwegian character substitutions
def could_be_norwegian_equivalent(str1, str2):
    """
    Check if two strings could be equivalent with common Norwegian character substitutions.
    For example, "forer" could be equivalent to "fører" because "ø" is often replaced with "o".
    """
    if not str1 or not str2:
        return False
    
    # Direct comparison
    if str1.lower() == str2.lower():
        return True
    
    # Normalize both strings
    norm1 = normalize_norwegian(str1)
    norm2 = normalize_norwegian(str2)
    
    # Compare normalized versions
    if norm1 == norm2:
        return True
    
    # Try replacing ASCII equivalents back to Norwegian characters
    # This handles cases where "forer" should match "fører"
    test1 = str1.lower().replace('o', 'ø').replace('ae', 'æ').replace('a', 'å')
    test2 = str2.lower().replace('o', 'ø').replace('ae', 'æ').replace('a', 'å')
    
    # If either replacement matches
    if test1 == str2.lower() or test2 == str1.lower():
        return True
    
    # Try partial replacements for common cases
    common_replacements = [
        ('o', 'ø'),
        ('a', 'å'),
        ('ae', 'æ'),
        ('oe', 'ø'),
    ]
    
    # Try each replacement individually
    for ascii_char, norwegian_char in common_replacements:
        if str1.lower().replace(ascii_char, norwegian_char) == str2.lower():
            return True
        if str2.lower().replace(ascii_char, norwegian_char) == str1.lower():
            return True
    
    return False

# Define a custom secure_filename function that preserves Norwegian characters
def secure_filename(filename):
    """
    Custom secure_filename that preserves Norwegian characters (øæå)
    while handling control characters and special symbols
    """
    if not filename:
        return ""
    
    # First, normalize Unicode characters
    filename = unicodedata.normalize('NFC', filename)
    
    # Keep Norwegian characters øæå (both lowercase and uppercase)
    keep_chars = 'øæåØÆÅ'
    
    # Replace spaces with underscore
    filename = filename.replace(' ', '_')
    
    # Remove control characters first
    filename = ''.join(c for c in filename if ord(c) >= 32 or c in keep_chars)
    
    # Convert to ASCII for non-Norwegian characters, preserving Norwegian ones
    result = ""
    for char in filename:
        if char.isalnum() or char == '.' or char == '_' or char == '-' or char in keep_chars:
            result += char
        else:
            # Replace other special characters with underscore
            result += '_'
    
    # Remove leading/trailing dots and ensure we have a valid filename
    while result.startswith('.'):
        result = result[1:]
    while result.endswith('.') and result != '.':
        result = result[:-1]
    
    # If result is empty, provide a placeholder
    if not result:
        result = 'unnamed_file'
        
    return result 