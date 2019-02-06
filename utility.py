"""
Various utility functions for activityReader project.

Copyright 2018 Terry Patterson

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


def get_user_confirmation(message):
    """
    Get an affarmtive response from the user.

    Args:
        message (string): The message to ask the user.
    Return:
        A boolean indicate user agreement.
    """
    vaild_postive = ["y", "yes"]
    vaild_negative = ["n", "no"]
    vaild_input_recived = False
    while(not vaild_input_recived):
        user_response = input(message)
        user_response_folded = user_response.casefold()
        if user_response_folded in vaild_postive:
            vaild_input_recived = True
            return True
        elif user_response_folded in vaild_negative:
            vaild_input_recived = True
            return False
        else:
            message += f"\n{user_response} is not vaild please enter  Y or N: "
