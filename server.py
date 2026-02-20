import os

def update_html_path(file_path):
    # Read the content of the HTML file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the replacement is already done
    if "/soa/soa/static/app/" in content:
        print("File already updated. No changes made.")
        return
    
    # Replace /static/app/ with /soa/soa/static/app/
    if "/static/app/" in content:
        content = content.replace("/static/app/", "/soa/soa/static/app/")
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("File updated successfully.")
    
    else:
        print("No /static/app/ paths found. No changes made.")


folder_path = r'app/templates'
for file in ['index.html', 'extract.html', 'client.html', 'dashboard.html', 'payment_aging.html', 'payment_advice.html', 'users.html',
             'approval.html', 'login.html', 'users1.html', 'role.html', 'settings.html', 'permission.html', 'menu.html', 'button.html', 
             "base.html", 'category.html', 'forgot_password.html', 'reset_password.html', 'profile.html', 'client_manage.html', 'extract_v2.html'
             ]:
    file_path = os.path.join(folder_path, file)
    print(file_path)
# Example usage
    update_html_path(file_path)

print('====='* 10,'/  STATIC FILES  /', '====='* 10 )
folder_path = r'app/static/app'
for file in [ 'users1.js', 'profile.js', 'client_manage.js', 'extract_v2.js'
             ]:
    file_path = os.path.join(folder_path, file)
    print(file_path)
# Example usage
    update_html_path(file_path)
