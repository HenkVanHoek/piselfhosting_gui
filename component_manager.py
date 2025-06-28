import json
import os
import re  # For validating component_id


class ComponentManager:
    """
    Manages loading, saving, and validating component_metadata.json.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.components_data = self._load_data()

    def _load_data(self):
        """Loads metadata from the JSON file."""
        if not os.path.exists(self.filepath):
            # If the file does not exist, return an empty dictionary
            # and print a warning
            print(f"File '{self.filepath}' not found, starting with empty data.")
            return {}
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                # Check if the loaded data is a dictionary
                if not isinstance(data, dict):
                    raise ValueError("File does not contain a valid JSON dictionary.")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file '{self.filepath}': {e}")
        except Exception as e:
            raise ValueError(f"Error loading file '{self.filepath}': {e}")

    def _save_data(self):
        """Saves metadata to the JSON file."""
        try:
            # Write to a temporary file first and then rename
            # This prevents corruption of the original file in case of a write error
            temp_filepath = self.filepath + '.tmp'
            with open(temp_filepath, 'w') as f:
                json.dump(self.components_data, f, indent=2)
            os.replace(temp_filepath, self.filepath)  # Replace the original file
        except Exception as e:
            raise ValueError(f"Error saving file '{self.filepath}': {e}")

    def get_all_components(self):
        """Returns all component data."""
        return self.components_data

    def get_component(self, component_id):
        """Returns data for a specific component."""
        return self.components_data.get(component_id)

    def _validate_component_id(self, component_id, is_new=True):
        """Validates the component_id."""
        if not component_id:
            raise ValueError("Component ID cannot be empty.")
        if not re.match(r"^[a-z0-9-]+$", component_id):
            raise ValueError("Component ID can only contain lowercase letters, numbers, and hyphens.")
        if is_new and component_id in self.components_data:
            raise ValueError(f"Component ID '{component_id}' already exists.")
        if not is_new and component_id not in self.components_data:
            raise ValueError(f"Component ID '{component_id}' does not exist.")

    def _validate_ui_port_uniqueness(self, new_ui_port, component_id_being_edited=None):
        """Validates that the UI port is unique."""
        if new_ui_port is None:
            return  # No UI port, no uniqueness check needed

        for comp_id, comp_data in self.components_data.items():
            # Skip the component being edited during the check
            if comp_id == component_id_being_edited:
                continue

            if comp_data.get('has_ui') and comp_data.get('ui_port') == new_ui_port:
                raise ValueError(
                    f"UI port {new_ui_port} is already in use by component '{comp_id}'. Ports must be unique.")

    def _validate_single_reverse_proxy(self, new_is_reverse_proxy_value, component_id_being_edited=None):
        """Validates that at most one reverse proxy is selected."""
        if not new_is_reverse_proxy_value:
            return  # If the new value is False, there is no conflict with this component

        # Check if another reverse proxy already exists
        for comp_id, comp_data in self.components_data.items():
            if comp_id == component_id_being_edited:
                continue  # Skip the component being edited

            if comp_data.get('is_reverse_proxy'):
                raise ValueError(
                    f"Component '{comp_id}' is already selected as a reverse proxy. Maximum one reverse proxy allowed.")

    def _validate_dashy_tile_fields(self, component_data):
        """Validates Dashy tile-related fields if 'has_ui' is true."""
        if component_data.get('has_ui'):
            if component_data.get('ui_port') is None:
                raise ValueError("UI Port is required if 'Has Web Interface' is selected.")
            if not isinstance(component_data.get('ui_port'), int) or not (1 <= component_data['ui_port'] <= 65535):
                raise ValueError("UI Port must be an integer between 1 and 65535.")
            if not component_data.get('protocol'):
                raise ValueError("Protocol is required if 'Has Web Interface' is selected.")
            if component_data.get('protocol') not in ['http', 'https']:
                raise ValueError("Protocol must be 'http' or 'https'.")
            if not component_data.get('icon'):
                raise ValueError("Icon is required if 'Has Web Interface' is selected.")
            if not component_data.get('dashy_tile_section'):
                raise ValueError("Dashy Section is required if 'Has Web Interface' is selected.")
            if component_data.get('dashy_tile_url_suffix') is None:  # Can be empty string, but not None
                raise ValueError("Dashy URL Suffix is required if 'Has Web Interface' is selected.")

    def add_component(self, component_id, data):
        """Adds a component after validation."""
        self._validate_component_id(component_id, is_new=True)

        # Temporarily add the new component for uniqueness checks
        # We will only add it permanently if everything is valid
        temp_data = self.components_data.copy()
        temp_data[component_id] = data  # Add the new data for validation context

        # Perform validations on the combined dataset
        if data.get('has_ui'):
            # Pass manager.get_all_components() and the current ID to validation functions
            # for correct context. These methods were previously missing this context.
            # Reworking the manager to allow external validation with full data.
            # The current validation methods implicitly use self.components_data,
            # so for 'add', it needs to be careful not to include the new component
            # in the check for other components.
            # The current implementation of _validate_ui_port_uniqueness and
            # _validate_single_reverse_proxy already handle this with `component_id_being_edited=None` for adds.
            self._validate_ui_port_uniqueness(data.get('ui_port'), component_id_being_edited=None)
            self._validate_dashy_tile_fields(data)

        if data.get('is_reverse_proxy'):
            self._validate_single_reverse_proxy(data.get('is_reverse_proxy'), component_id_being_edited=None)

        # General field validation
        if not data.get('name'):
            raise ValueError("Component name is required.")

        # All is valid, now truly add
        self.components_data[component_id] = data
        self._save_data()

    def update_component(self, component_id, data):
        """Updates a component after validation."""
        self._validate_component_id(component_id, is_new=False)  # Check if ID exists

        # Perform validations on the combined dataset (including the new data)
        if data.get('has_ui'):
            self._validate_ui_port_uniqueness(data.get('ui_port'), component_id_being_edited=component_id)
            self._validate_dashy_tile_fields(data)

        if data.get('is_reverse_proxy'):
            self._validate_single_reverse_proxy(data.get('is_reverse_proxy'), component_id_being_edited=component_id)

        # General field validation
        if not data.get('name'):
            raise ValueError("Component name is required.")

        # All is valid, now truly update
        self.components_data[component_id] = data
        self._save_data()

    def delete_component(self, component_id):
        """Deletes a component."""
        if component_id not in self.components_data:
            raise ValueError(f"Component ID '{component_id}' not found for deletion.")
        del self.components_data[component_id]
        self._save_data()

