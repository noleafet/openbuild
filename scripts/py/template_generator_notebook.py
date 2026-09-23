import marimo

__generated_with = "0.24.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from template.generator import DEFAULT_YML_DIR, DEFAULT_PROJECT_ENV, REPO_ROOT, TemplateGenerator

    yml_dir = mo.ui.text(value=str(DEFAULT_YML_DIR), label="Yaml directory")
    project_env = mo.ui.text(value=str(DEFAULT_PROJECT_ENV), label="Project environment")
    force = mo.ui.checkbox(value=False, label="Overwrite existing files")
    generate = mo.ui.run_button(label="Generate Compose files")

    mo.vstack([
        yml_dir,
        project_env,
        force,
        generate
    ])
    return TemplateGenerator, force, generate, mo, project_env, yml_dir


@app.cell
def _(TemplateGenerator, force, generate, mo, project_env, yml_dir):
    if generate.value:
        generated_files = TemplateGenerator.generate_compose_files(
            output_dir=yml_dir.value,
            force=force.value,
        )
        if generated_files:
            yml_result = mo.md(f"YML generated:\n{'\n'.join(f'- `{path}`' for path in generated_files)}")
        else:
            yml_result = mo.md("No yml files were generated.")

        env_file = TemplateGenerator.generate_project_env_file(
            yml_dir=yml_dir.value, 
            output_file=project_env.value)
        if env_file:
            env_result = mo.md(f"Env generated: {env_file}")
        else:
            env_result = mo.md("No env file generated.")
    else:
        yml_result = mo.md("Choose the output directory and click **Generate Compose files**.")
        env_result = mo.md("")

    env_result, yml_result
    return 


if __name__ == "__main__":
    app.run()
