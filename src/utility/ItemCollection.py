from src.utility.Config import Config
from src.utility.Utility import Utility
import json
from copy import deepcopy

class ItemCollection:
    """ Manages the reading and creation of multiple items (like light sources or cam poses) from config or file. """

    def __init__(self, add_item_func, default_item_parameters):
        """
        :param add_item_func: A function which adds a new item. It only should have one parameter which is the configuration item.
        :param default_item_parameters: A dict containing the default parameters which should be applied across all items.
        """
        self.add_item_func = add_item_func
        self.default_item_parameters = default_item_parameters

    def add_items_from_file(self, path, file_format, number_of_arguments_per_parameter):
        """ Adds one item per line of the given file.

        :param path: The path of the file to read.
        :param file_format: Specifies how each line is formatted
        :param number_of_arguments_per_parameter: A dict specifying the length of parameters that require more than one argument.
        """
        file_format = file_format.split()
        # Calc the total number of arguments necessary per line (used for validating the file)
        number_of_arguments = sum([self._length_of_parameter(parameter_name, number_of_arguments_per_parameter) for parameter_name in file_format])

        # Read in file and split lines up into arguments
        for arguments in self._collect_arguments_from_file(path, file_format, number_of_arguments):
            # Parse parameters from arguments and add new item
            self.add_item(self._parse_arguments_from_file(arguments, file_format, number_of_arguments_per_parameter))

    def add_items_from_dicts(self, dicts):
        """ Adds items from a list of dicts.

        Every dict specifies the parameters of one new item.

        :param dicts: The list of dicts.
        """
        for parameters in dicts:
            self.add_item(parameters)

    def add_item(self, parameters):
        """ Adds a new item based on the given parameters.

        :param parameters: A dict specifying the parameters.
        """
        # Start with the default parameters
        data = deepcopy(self.default_item_parameters)
        # Overwrite default parameter values with specific parameters for this item
        data = Utility.merge_dicts(parameters, data)
        # Create config object
        config = Config(data)
        # Call function to add new item
        self.add_item_func(config)

    def _parse_arguments_from_file(self, arguments, file_format, number_of_arguments_per_parameter):
        """ Sets the parameters using the given arguments.

        :param arguments: A list of arguments read in from the file.
        :param file_format: Specifies how the arguments should be mapped to parameters.
        :param number_of_arguments_per_parameter: A dicts which maps parameter names to their required number of arguments.
        :return: A dict containing the parameters specified by the given arguments.
        """
        data = {}
        # Go through all configured parameters, set current one using N next argument
        for parameter_name in file_format:
            # Check if we should just skip the next parameter
            if parameter_name != "_":
                # Lookup how many arguments the parameter consumes.
                parameter_length = self._length_of_parameter(parameter_name, number_of_arguments_per_parameter)
                # Read in the next N arguments
                if parameter_length > 1:
                    data[parameter_name] = arguments[:parameter_length]
                else:
                    data[parameter_name] = arguments[0]
                arguments = arguments[parameter_length:]
            else:
                arguments = arguments[1:]

        return data

    def _length_of_parameter(self, parameter_name, number_of_arguments_per_parameter):
        """ Returns how many arguments the given parameter expects.

        :param parameter_name: The name of the parameter.
        :param number_of_arguments_per_parameter: Dict where {key:value} pairs are {name of the parameter:expected number of arguments} pairs.
        :return: The expected number of arguments
        """
        # If not specified, 1 is assumed.
        if parameter_name in number_of_arguments_per_parameter:
            return number_of_arguments_per_parameter[parameter_name]
        else:
            return 1

    def _collect_arguments_from_file(self, path, file_format, number_of_arguments):
        """ Reads in all lines of the given file and returns them as a list of lists of arguments

        This method also checks is the lines match the configured file format.

        :param path: The path of the file.
        :param file_format: Specifies how the arguments should be mapped to parameters.
        :param number_of_arguments: The total number of arguments required per line.
        :return: A list of lists of arguments
        """
        cam_poses = []
        if path != "":
            with open(Utility.resolve_path(path)) as f:
                lines = f.readlines()
                # remove all empty lines
                lines = [line for line in lines if len(line.strip()) > 3]

                for line in lines:
                    # Split line into separate arguments
                    cam_args = line.strip().split()
                    # Make sure the arguments match the configured file format
                    if len(cam_args) != number_of_arguments:
                        raise Exception("A line in the given cam pose file does not match the configured file format:\n" + line.strip() + " (Number of values: " + str(len(cam_args)) + ")\n" + str(file_format) + " (Number of values: " + str(number_of_arguments) + ")")

                    # Parse arguments in line using json. (In this way "test" will be mapped to a string, while 42 will be mapped to an integer)
                    cam_poses.append([json.loads(x) for x in cam_args])

        return cam_poses