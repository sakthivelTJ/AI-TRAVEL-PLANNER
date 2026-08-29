import sys
sys.path.append('.')
from app import app

print("Checking all template files for Jinja2 syntax errors...")
with app.app_context():
    # Attempt to compile and load all templates used in the app
    templates = ['index.html', 'planner.html', 'plan.html', 'dashboard.html', 'login.html', 'register.html']
    success = True
    for template_name in templates:
        try:
            app.jinja_env.get_template(template_name)
            print(f"[OK] {template_name} compiles successfully.")
        except Exception as e:
            print(f"[FAIL] {template_name} failed to compile: {e}")
            success = False
            
    if not success:
        sys.exit(1)
            
print("All templates compile successfully!")
