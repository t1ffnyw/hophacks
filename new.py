# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.24.2",
# ]
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    print("hello")
    return


if __name__ == "__main__":
    app.run()
