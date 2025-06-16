#!/usr/bin/env python3
"""
Program name: pos_list.py

This program creates a correctly formated `.pos` file to use with Micro-Manager.
The list of (x,y) positions is created from two arrays, user defined bellow.
The output file is saved in a user-defined location.

Run this file with
    python3 pos_list.py ./setting_file.txt ./Output.txt --options

options :
---------
    z_stack : bool, optionnal, default False
        If z_stack is True, the z values will be considered as a stack, meaning
        each (x,y) position will be associated to each z value.
        In z_stack mode, no noiise will be applied.

    noise_width : float, default 0.
        width of the noise added to z

    noise_type : str, either None, "white" or "oscil", default None
        selects the type of noise to use. It can be None.

    mode : string, default "snake"
        string indicating the method used to sort the positions. Options are
            "standard" : x1,y1 // x1,y2 // x2,y1 // x2,y2
            "reversed" : x1,y1 // x2,y1 // x1,y2 // x2,y2
            "snake"    : x1,y1 // x1,y2 // x2,y2 // x2,y1
            "random"

    compatibility_MDA : bool, default True
        If True, forces the output file to contain enough noise to trigger the
        displacement of the xy stage at each step, by slightly moving the z stage.
        This circumvents a bug present in Micro Manager.


Author: Yohann Faure
Date: 2024-11-04
"""

import numpy as np
import random
import warnings
import sys
import argparse



## Reference strings to be formated

# string for each position
str_ref = """        {{
          "DefaultXYStage": {{
            "type": "STRING",
            "scalar": "XY Stage"
          }},
          "DefaultZStage": {{
            "type": "STRING",
            "scalar": "PIZStage"
          }},
          "DevicePositions": {{
            "type": "PROPERTY_MAP",
            "array": [
              {{
                "Device": {{
                  "type": "STRING",
                  "scalar": "XY Stage"
                }},
                "Position_um": {{
                  "type": "DOUBLE",
                  "array": [
                    {},
                    {}
                  ]
                }}
              }}
            ]
          }},
          "GridCol": {{
            "type": "INTEGER",
            "scalar": 0
          }},
          "GridRow": {{
            "type": "INTEGER",
            "scalar": 0
          }},
          "Label": {{
            "type": "STRING",
            "scalar": "Pos{}"
          }},
          "Properties": {{
            "type": "PROPERTY_MAP",
            "scalar": {{}}
          }}
        }}"""

# string for each position
str_ref_with_z = """        {{
          "DefaultXYStage": {{
            "type": "STRING",
            "scalar": "XY Stage"
          }},
          "DefaultZStage": {{
            "type": "STRING",
            "scalar": "PIZStage"
          }},
          "DevicePositions": {{
            "type": "PROPERTY_MAP",
            "array": [
              {{
                "Device": {{
                  "type": "STRING",
                  "scalar": "PIZStage"
                }},
                "Position_um": {{
                  "type": "DOUBLE",
                  "array": [
                    {}
                  ]
                }}
              }},
              {{
                "Device": {{
                  "type": "STRING",
                  "scalar": "XY Stage"
                }},
                "Position_um": {{
                  "type": "DOUBLE",
                  "array": [
                    {},
                    {}
                  ]
                }}
              }}
            ]
          }},
          "GridCol": {{
            "type": "INTEGER",
            "scalar": 0
          }},
          "GridRow": {{
            "type": "INTEGER",
            "scalar": 0
          }},
          "Label": {{
            "type": "STRING",
            "scalar": "Pos{}"
          }},
          "Properties": {{
            "type": "PROPERTY_MAP",
            "scalar": {{}}
          }}
        }}"""





# beggining string
str_main_1 = """{
  "encoding": "UTF-8",
  "format": "Micro-Manager Property Map",
  "major_version": 2,
  "minor_version": 0,
  "map": {
    "StagePositions": {
      "type": "PROPERTY_MAP",
      "array": [
"""

# ending string
str_main_2 = """
      ]
    }
  }
}"""




## Functions

def create_pairs(x_arr,y_arr,mode="standard"):
    """
    Create an array containing each pair [x_i, y_j]
    for x_i in x_arr and y_j in y_arr.

    Parameters:
    ----------
    x_arr : np.ndarray (n,)
        1-dimensional numpy array containing values for x.

    y_arr : np.ndarray (m,)
        1-dimensional numpy array containing values for y.

    mode : string
        string indicating the method used to sort the positions. Options are
            "standard" : x1,y1 // x1,y2 // x2,y1 // x2,y2
            "reversed" : x1,y1 // x2,y1 // x1,y2 // x2,y2
            "snake"    : x1,y1 // x1,y2 // x2,y2 // x2,y1
            "random"

    Returns:
    -------
    np.ndarray (n*m, 2)
        Array containing all combinations of pairs [x_i, y_j].
    """
    pairs = []

    if mode == "reversed":
        for y in y_arr:
            for x in x_arr:
                pairs.append([x,y])

    elif mode == "snake":
        direction = 1
        for x in x_arr:
            if direction == 1:
                for y in y_arr:
                    pairs.append([x,y])
                direction = -1
            else :
                for y in y_arr[::-1]:
                    pairs.append([x,y])
                direction = 1
    else :
        for x in x_arr:
            for y in y_arr:
                pairs.append([x,y])

    if mode == "random":
        random.shuffle(pairs)

    pairs = np.array(pairs)

    return pairs



def create_new_position_string(pair, i=0, z=None):
    """
    Creates a formatted string specific to a position based on
    a pair of values (x, y) and an optional index.

    Parameters
    ----------
    pair : tuple
        A tuple (x, y) containing two values

    i : int, optional
        An optional index value to be included in the formatted string
        (default is 0).

    z : float, optional
        An optional z value for the position.
        If None is given, the position string will simply be z-independant.


    Returns
    -------
    str_pair
        A formatted string specific to that position.

    Notes
    -----
    `str_ref` is a predefined format string.
    """
    x, y = pair
    if not (z is None):
        str_pair = str_ref_with_z.format(z,x,y,i)
    else:
        str_pair = str_ref.format(x, y, i)
    return str_pair



def create_full_string(positions, z=None, z_stack = False, noise_width = 0, noise_type = None):
    """
    Creates a full formatted string by concatenating position-specific strings
    for each element in a list of positions.
    Adding noise on z is a usefull trick to compensate a bug in Micro-manager.

    Parameters
    ----------
    positions : list of tuples (n, 2)
        A list of tuples where each tuple represents a position (x, y)

    z : float or np.ndarray (n,), optional
        An optional z value for the positions.
        If None is given, the position string will simply be z-independant.
        If an array is given, every position will be given a z-position.
        If an array is given, every position will be given a z-position.

    z_stack : bool, optionnal
        If z_stack is True, the z values will be considered as a stack, meaning
        each (x,y) position will be associated to each z value.
        In z_stack mode, no noiise will be applied.

    noise_width : float
        width of the noise added to z

    noise_type : str, either None, "white" or "oscil"
        selects the type of noise to use. It can be None.

    Returns
    -------
    str
        A full string constructed.

    Notes
    -----
    `str_main_1` is added at the beginning of the concatenation of the positions
    strings, and `str_main_2` is appended at the end.
    """
    if not z_stack:
        if z:
            z = np.array(z)
            try :
                z_arr = np.zeros(len(positions)) + z
            except :
                raise Exception("z is of the wrong dimension. Did you try to create a z_stack? Try adding z_stack=True")


            if noise_type == "white":
                z_arr += (np.random.random(len(positions))-0.5)*noise_width

                # adding that avoids getting twice the same z value
                for k in range(len(z_arr)-1):
                    if abs(z_arr[k]-z_arr[k+1])<0.0002:
                        if z_arr[k]<z_arr[k+1]:
                            z_arr[k+1]+=0.0002
                        else:
                            z_arr[k+1]-=0.0002


            elif noise_type == "oscil":
                z_arr += (np.array([i%2 for i in range(len(positions))]))*noise_width

            # rounding for text file format
            z_arr = z_arr.round(4)

        full_str = str_main_1
        for i in range(len(positions)):
            if not (z is None):
                full_str += create_new_position_string(positions[i], i, z_arr[i])
            else :
                full_str += create_new_position_string(positions[i], i)
            if i < len(positions) - 1:
                full_str += ",\n"
        full_str += str_main_2

    else :#z_stack
        if (z is None):
            raise Exception("to create a z_stack, a z array has to be given")
        if  ( noise_width != 0) or ( not (noise_type is None) ):
            warnings.warn("Warning : using noise with z_stack mode is prohibited. Noise will not be added.")

        full_str = str_main_1
        for i in range(len(positions)):
            for j in range(len(z)):
                full_str += create_new_position_string(positions[i], i*len(z)+j, z[j])
                if i < len(positions) - 1 or j < len(z) -1:
                    full_str += ",\n"
        full_str += str_main_2

    return full_str




def generate_pos_file(x_arr, y_arr, z, location,
                z_stack=False,
                noise_width = 0,
                noise_type = None,
                mode="standard",
                compatibility_MDA = True):
    """
    main function that calls all the others.

    x_arr : np.ndarray (n,)
        1-dimensional numpy array containing values for x.

    y_arr : np.ndarray (m,)
        1-dimensional numpy array containing values for y.

    z : float or np.ndarray (n,)
        A z value for the positions.
        If a float is given, the z-position of every step will be the same.
        If an array is given, every position will be given a z-position.

    z_stack : bool, optionnal
        If z_stack is True, the z values will be considered as a stack, meaning
        each (x,y) position will be associated to each z value.
        In z_stack mode, no noiise will be applied.

    noise_width : float
        width of the noise added to z

    noise_type : str, either None, "white" or "oscil"
        selects the type of noise to use. It can be None.

    mode : string
        string indicating the method used to sort the positions. Options are
            "standard" : x1,y1 // x1,y2 // x2,y1 // x2,y2
            "reversed" : x1,y1 // x2,y1 // x1,y2 // x2,y2
            "snake"    : x1,y1 // x1,y2 // x2,y2 // x2,y1
            "random"

    compatibility_MDA : bool
        If True, forces the output file to contain enough noise to trigger the
        displacement of the xy stage at each step, by slightly moving the z stage.
        This circumvents a bug present in Micro Manager.

    """
    positions = create_pairs(x_arr,y_arr, mode = mode)

    if compatibility_MDA:
        if noise_type is None:
            noise_type = "oscil"
        if noise_width < 0.0002:
            noise_width=0.0002

    full_string = create_full_string(positions, z = z, z_stack=z_stack, noise_width = noise_width, noise_type = noise_type)


    with open(location, "w") as text_file:
        text_file.write(full_string)

    return(None)






## Execution


if __name__ == "__main__":

    UNSPECIFIED = object()

    parser = argparse.ArgumentParser(description='This script create a position list to use with the MDA of MicroManager.')

    parser.add_argument("setting_file", type=str, help="")
    parser.add_argument("output_location", type=str, help="")


    parser.add_argument(
        "--z_stack",
        action="store_true",
        default=UNSPECIFIED,
        help="Enable z_stack mode (default: False)."
    )
    parser.add_argument(
        "--noise_width",
        type=int,
        default=UNSPECIFIED,
        help="Width of the noise to be applied (default: 0)."
    )
    parser.add_argument(
        "--noise_type",
        type=str,
        choices=["white", "oscil"],
        default=UNSPECIFIED,
        help="Type of noise to apply (default: None). Choose from 'white' or 'oscil'."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["snake", "standard", "random", "reversed"],
        default=UNSPECIFIED,
        help="Scanning mode to use (default: 'snake'). Options: 'snake', 'standard', 'reversed' or 'random'."
    )
    parser.add_argument(
        "--compatibility_MDA",
        action="store_true",
        default=UNSPECIFIED,
        help="Enable compatibility with MDA (default: True)."
    )

    args = parser.parse_args()

    setting_file = args.setting_file
    output_location = args.output_location

    # parameters (overwriten by execution arguments if any)
    z_stack = True
    noise_width = 0
    noise_type = None
    mode="snake"
    compatibility_MDA = True

    with open(setting_file, "r") as file:
        code = file.read()
    exec(code)


    # Default values for the arguments, from the params file
    DEFAULT_Z_STACK           = z_stack
    DEFAULT_NOISE_WIDTH       = noise_width
    DEFAULT_NOISE_TYPE        = noise_type
    DEFAULT_MODE              = mode
    DEFAULT_COMPATIBILITY_MDA = compatibility_MDA



    # Check and assign values only if they were explicitly provided by the user
    z_stack            = args.z_stack if args.z_stack is not UNSPECIFIED else                       DEFAULT_Z_STACK
    noise_width        = args.noise_width if args.noise_width is not UNSPECIFIED else               DEFAULT_NOISE_WIDTH
    noise_type         = args.noise_type if args.noise_type is not UNSPECIFIED else                 DEFAULT_NOISE_TYPE
    mode               = args.mode if args.mode is not UNSPECIFIED else                             DEFAULT_MODE
    compatibility_MDA  = args.compatibility_MDA if args.compatibility_MDA is not UNSPECIFIED else   DEFAULT_COMPATIBILITY_MDA



    generate_pos_file(x_arr, y_arr, z, output_location,
                z_stack=z_stack,
                noise_width = noise_width,
                noise_type = noise_type,
                mode=mode,
                compatibility_MDA = compatibility_MDA)


else :
    # change your parameters here

    # positions in µm
    x_arr = np.linspace(-10,10,5)
    y_arr = np.linspace(-10,10,5)

    # parameters
    z = 40
    z_stack = False
    noise_width = 0
    noise_type = None
    mode="snake"
    compatibility_MDA = True


    # location
    #location = "/home/fy106182/Documents/ATER/recherche/xystage/Output.pos"
    location = "C:/Users/adminlocal/Documents/QUMIN/xystage/Output.pos"





    generate_pos_file(x_arr, y_arr, z, location,
                z_stack=z_stack,
                noise_width = noise_width,
                noise_type = noise_type,
                mode=mode,
                compatibility_MDA = compatibility_MDA)












