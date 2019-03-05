
def decorator(param):
    def outer(func):
        def inner(func_arg):
            print(f"inner: {func_arg}, outer: {func}, decorator: {param}")
            print(f"func returned: {func(func_arg)}")
        print(f"outer {func}, decorator: {param}")
        return inner
    print(f"decorator {param}")
    return outer

@decorator("hello")
def do_stuff(arg):
    print(f"inside do stuff {arg}")
    return "return stuff"

print("......")
do_stuff("roar")
