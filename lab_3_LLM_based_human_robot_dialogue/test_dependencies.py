import importlib
import os

dependencies = [
    ("os", "os"),
    ("time", "time"),
    ("paramiko", "paramiko"),
    ("qi", "qi"),
    ("openai", "openai"),
    ("dotenv", "python-dotenv"),
    ("json", "json")
]

def test_dependencies():
    print(f"{'Target':<16} | {'Status':<10} | {'Details'}")
    print("-" * 65)

    all_passed = True

    # Check Python dependencies
    for module_name, pip_name in dependencies:
        try:
            importlib.import_module(module_name)
            status = "Installed"
            details = "OK"

            if module_name == "dotenv":
                from dotenv import load_dotenv
                load_dotenv()
                details = "load_dotenv available"
            elif module_name == "openai":
                from openai import OpenAI
                _ = OpenAI.__name__
                details = "OpenAI class ready"
            elif module_name == "paramiko":
                import paramiko
                _ = paramiko.SSHClient()
                details = "SSHClient instantiated"
            elif module_name == "qi":
                import qi
                details = "qi module imported"
        except ImportError:
            status = "Missing"
            details = f"Run: pip install {pip_name}"
            all_passed = False
        except Exception as e:
            status = "Error"
            details = str(e)
            all_passed = False

        print(f"{module_name:<16} | {status:<10} | {details}")

    print("-" * 65)

    # Check .env in parent directory for OPENAI_API_KEY using standard os module
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    parent_env_path = os.path.join(parent_dir, ".env")

    env_status = "Checked"

    if os.path.exists(parent_env_path):
        try:
            from dotenv import dotenv_values
            env_vars = dotenv_values(parent_env_path)
            api_key = env_vars.get("OPENAI_API_KEY")

            if api_key:
                env_status = "Found"
                env_details = "OPENAI_API_KEY present in parent .env"
            else:
                env_status = "Invalid"
                env_details = ".env exists, but OPENAI_API_KEY is missing/empty"
                all_passed = False
        except Exception as e:
            env_status = "Error"
            env_details = f"Failed to parse .env: {e}"
            all_passed = False
    else:
        env_status = "Missing"
        env_details = f"No .env file found in parent directory ({parent_dir})"
        all_passed = False

    print(f"{'Parent .env':<16} | {env_status:<10} | {env_details}")

    if all_passed:
        print("\nAll target dependencies and environment configurations passed.")
    else:
        print("\nSome checks failed verification.")

if __name__ == "__main__":
    test_dependencies()
