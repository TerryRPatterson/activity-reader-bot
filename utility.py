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
