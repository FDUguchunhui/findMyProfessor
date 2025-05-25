from src.faculty_advisor import create_gradio_interface

if __name__ == "__main__":
    interface = create_gradio_interface()
    interface.launch(share=True)  # Set share=True to create a public link