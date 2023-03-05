# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai
import sys


def call(seed):
    openai.api_key = seed
    answer = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": """"I disagree. The war bad for the humanity. (list of causes)"
                Please, rewrite"""}
            ]
    )
    print(answer['choices'][0]['message']['content'])
    print('done')


def main():
    # get sid from the parameter
    seed = sys.argv[1]
    call(seed)


if __name__ == "__main__":
    main()
