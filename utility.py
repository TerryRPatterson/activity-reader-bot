"""
MIT License

Copyright (c) 2018 Terry Patterson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

def get_user_confirmation(message):
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
