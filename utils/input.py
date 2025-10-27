def prompt_input(prompt: str, required: bool = True, cast_type=None, retry_limit: int = 3):
    for attempt in range(retry_limit):
        try:
            value = input(prompt).strip()
            if required and not value:
                print("❌ Input is required.")
                continue
            if cast_type:
                return cast_type(value)
            return value
        except ValueError:
            print(f"❌ Invalid input. Expected {cast_type.__name__}.")
    raise ValueError("Too many invalid attempts.")