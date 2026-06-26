# Final JSON formatter
def build_report(
    project_data,
    llm_result
):

    return {

        "project_summary":
            llm_result["project_summary"],

        "skills":
            llm_result["skills"],

        "questions":
            llm_result["questions"],

        "project_statistics": {

            "files_analyzed":
                len(
                    project_data["file_tree"]
                ),

            "dependencies_found":
                len(
                    project_data["dependencies"]
                ),

            "code_samples_used":
                len(
                    project_data["code_samples"]
                )
        }
    }