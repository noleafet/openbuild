import marimo

__generated_with = "0.24.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from devops_compose_yaml_generator.catalog import BASE_OUTPUT_DIR
    from devops_compose_yaml_generator.generator import DevOpsYamlGenerator

    output_dir = mo.ui.text(value=str(BASE_OUTPUT_DIR), label="Output directory")
    force = mo.ui.checkbox(value=False, label="Overwrite existing files")
    generate = mo.ui.run_button(label="Generate Compose files")

    mo.vstack([
        output_dir,
        force,
        generate
    ])
    return DevOpsYamlGenerator, force, generate, mo, output_dir


@app.cell
def _(DevOpsYamlGenerator, force, generate, mo, output_dir):
    if generate.value:
        generated_files = DevOpsYamlGenerator.generate_compose_files(
            output_dir=output_dir.value,
            force=force.value,
        )
        if generated_files:
            result = mo.md(
                "Generated:\n" + "\n".join(f"- `{path}`" for path in generated_files)
            )
        else:
            result = mo.md("No files were generated.")
    else:
        result = mo.md("Choose the output directory and click **Generate Compose files**.")
    return


if __name__ == "__main__":
    app.run()
