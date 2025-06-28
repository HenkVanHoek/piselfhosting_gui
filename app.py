import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash
import json
from component_manager import ComponentManager  # Import the ComponentManager class

# Define the path to the metadata file
# This file is assumed to be in the same directory as app.py
COMPONENTS_METADATA_FILE = 'components_metadata.json'

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random, secret key in a production scenario

# Initialize the ComponentManager
# This will load and validate the metadata file
try:
    manager = ComponentManager(COMPONENTS_METADATA_FILE)
except Exception as e:
    # If loading or initial validation fails, print an error message and exit the app
    print(f"FATAL ERROR: Could not initialize ComponentManager: {e}", file=sys.stderr)
    sys.exit(1)


@app.route('/')
def index():
    """Displays the main page with a list of components."""
    components = manager.get_all_components()
    return render_template('index.html', components=components)


@app.route('/add', methods=['GET', 'POST'])
def add_component():
    """Adds a new component."""
    if request.method == 'POST':
        # Get data from the form
        component_id = request.form.get('component_id')
        component_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'default_selected': 'default_selected' in request.form,
            'has_ui': 'has_ui' in request.form,
            'is_reverse_proxy': 'is_reverse_proxy' in request.form
        }

        # For UI-specific fields, only add if has_ui is true
        if component_data['has_ui']:
            component_data['ui_port'] = int(request.form.get('ui_port')) if request.form.get('ui_port') else None
            component_data['protocol'] = request.form.get('protocol')
            component_data['icon'] = request.form.get('icon')
            component_data['dashy_tile_section'] = request.form.get('dashy_tile_section')
            component_data['dashy_tile_url_suffix'] = request.form.get('dashy_tile_url_suffix')
            component_data['status_check'] = 'status_check' in request.form
        else:
            # If has_ui is false, remove UI-related fields to keep JSON clean
            component_data.pop('ui_port', None)
            component_data.pop('protocol', None)
            component_data.pop('icon', None)
            component_data.pop('dashy_tile_section', None)
            component_data.pop('dashy_tile_url_suffix', None)
            component_data.pop('status_check', None)

        # Try to add the component via the manager
        try:
            manager.add_component(component_id, component_data)
            flash(f"Component '{component_id}' successfully added.", 'success')
            return redirect(url_for('index'))
        except ValueError as e:
            # Display validation errors to the user
            flash(f"Error adding component: {e}", 'danger')
            # Render the form again with the entered data and error message
            return render_template('component_form.html', component=component_data, component_id=component_id,
                                   mode='add', manager=manager)

    # GET request: Display the empty add form
    return render_template('component_form.html', component={}, mode='add', manager=manager)


@app.route('/edit/<component_id>', methods=['GET', 'POST'])
def edit_component(component_id):
    """Edits an existing component."""
    component = manager.get_component(component_id)
    if not component:
        flash(f"Component '{component_id}' not found.", 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        updated_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'default_selected': 'default_selected' in request.form,
            'has_ui': 'has_ui' in request.form,
            'is_reverse_proxy': 'is_reverse_proxy' in request.form
        }

        # For UI-specific fields, only add if has_ui is true
        if updated_data['has_ui']:
            updated_data['ui_port'] = int(request.form.get('ui_port')) if request.form.get('ui_port') else None
            updated_data['protocol'] = request.form.get('protocol')
            updated_data['icon'] = request.form.get('icon')
            updated_data['dashy_tile_section'] = request.form.get('dashy_tile_section')
            updated_data['dashy_tile_url_suffix'] = request.form.get('dashy_tile_url_suffix')
            updated_data['status_check'] = 'status_check' in request.form
        else:
            # If has_ui is false, remove UI-related fields
            updated_data.pop('ui_port', None)
            updated_data.pop('protocol', None)
            updated_data.pop('icon', None)
            updated_data.pop('dashy_tile_section', None)
            updated_data.pop('dashy_tile_url_suffix', None)
            updated_data.pop('status_check', None)

        try:
            manager.update_component(component_id, updated_data)
            flash(f"Component '{component_id}' successfully updated.", 'success')
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f"Error updating component: {e}", 'danger')
            # Render the form again with the entered data and error message
            # Ensure the 'component_id' variable is passed
            return render_template('component_form.html', component=updated_data, component_id=component_id,
                                   mode='edit', manager=manager)

    # GET request: Display the edit form with existing data
    return render_template('component_form.html', component=component, component_id=component_id, mode='edit',
                           manager=manager)


@app.route('/delete/<component_id>', methods=['GET', 'POST'])  # Changed to include GET for debugging url_for
def delete_component(component_id):
    """Deletes a component."""
    try:
        manager.delete_component(component_id)
        flash(f"Component '{component_id}' successfully deleted.", 'success')
    except ValueError as e:
        flash(f"Error deleting component: {e}", 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Check if the metadata file exists, otherwise create an empty one
    if not os.path.exists(COMPONENTS_METADATA_FILE):
        print(f"'{COMPONENTS_METADATA_FILE}' not found, creating an empty file.")
        with open(COMPONENTS_METADATA_FILE, 'w') as f:
            json.dump({}, f, indent=2)

    app.run(debug=True, host='0.0.0.0', port=5000)  # Run the app on port 5000 in debug mode
