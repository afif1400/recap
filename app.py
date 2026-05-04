import gradio as gr


def respond(message, history):
    return "Recap is booting up. Architecture is being assembled."


with gr.Blocks(title="Recap") as demo:
    gr.Markdown("# Recap\n*Reads the whole chart so you don't have to.*")
    gr.ChatInterface(fn=respond)


if __name__ == "__main__":
    demo.launch()
