#!/usr/bin/env python3
"""
Program name: pos_list.py

This program creates a correctly formated `.pos` file to use with Micro-Manager.
The list of (x,y) positions is created from two arrays, user defined bellow.
The output file is saved in a user-defined location.

Author: Yohann Faure
Date: 2024-11-04
"""

import numpy as np
import random


## change your parameters here

# positions in µm
x_arr = np.linspace(-100,100,3)
y_arr = np.linspace(-100,100,3)

# location
location = "/home/fy106182/Documents/ATER/recherche/xystage/Output.pos"
#location = "C:/Users/adminlocal/Documents/QUMIN/test/Output.pos"




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
                direction = -1
    else :
        for x in x_arr:
            for y in y_arr:
                pairs.append([x,y])

    if mode == "random":
        pairs = random.shuffle(pairs)

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



def create_full_string(positions,z=None, noise_width = 0, noise_type = None):
    """
    Creates a full formatted string by concatenating position-specific strings
    for each element in a list of positions.
    Adding noise on z is a usefull trick to compensate a bug in Micro-manager.

    Parameters
    ----------
    positions : list of tuples
        A list of tuples where each tuple represents a position (x, y)

    z : float or np.ndarray (n,), optional
        An optional z value for the positions.
        If None is given, the position string will simply be z-independant.
        If an array is given, every position will be given a z-position.
        If a float is given, the z-position of every string will be randomized
        arond the given value to ensure movement (know bug for Micro-manager).

    noise_width : float
        width of the noise added to z

    noise_type : str, either "white" or "oscil"
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
    if z:
        z_arr = np.zeros(len(positions)) + z

        if noise_type == "white":
            z_arr += (np.random.random(len(positions))-0.5)*noise_width
            z_arr += np.array([i%2 for i in range(len(positions))])*0.0001 # adding that avoids getting twice the same z value

        elif noise_type == "oscil":
            z_arr += (np.array([i%2 for i in range(len(positions))])-0.5)*noise_width
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
    return full_str






## Execution


# minimal example that generated the same file as by Micro-manager
#positions = np.array([[0.0,0.0],[-500.0,0.0],[-1000.0,0.0]])


positions = create_pairs(x_arr,y_arr)

full_string = create_full_string(positions)#,z = 40, noise_width = 1, noise_type = "oscil")

with open(location, "w") as text_file:
    text_file.write(full_string)











