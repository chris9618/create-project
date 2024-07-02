import requests

# Define your GitLab token and base URL
access_token = 'your_access_token'
gitlab_url = 'https://gitlab.com/api/v4'

headers = {
    'Private-Token': access_token,
    'Content-Type': 'application/json'
}

def get_group_id(group_path):
    response = requests.get(f'{gitlab_url}/groups', headers=headers, params={'search': group_path})
    groups = response.json()
    for group in groups:
        if group['full_path'] == group_path:
            return group['id']
    return None

def create_group(name, parent_id=None):
    data = {
        'name': name,
        'path': name.lower().replace(' ', '-'),
        'parent_id': parent_id
    }
    response = requests.post(f'{gitlab_url}/groups', headers=headers, json=data)
    return response.json()

def get_project_id(project_name, namespace_id):
    response = requests.get(f'{gitlab_url}/projects', headers=headers, params={'search': project_name})
    projects = response.json()
    for project in projects:
        if project['name'] == project_name and project['namespace']['id'] == namespace_id:
            return project['id']
    return None

def create_project(name, namespace_id):
    data = {
        'name': name,
        'namespace_id': namespace_id
    }
    response = requests.post(f'{gitlab_url}/projects', headers=headers, json=data)
    return response.json()

def get_branch(project_id, branch_name):
    response = requests.get(f'{gitlab_url}/projects/{project_id}/repository/branches/{branch_name}', headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def create_branch(project_id, branch_name, ref='main'):
    data = {
        'branch': branch_name,
        'ref': ref
    }
    response = requests.post(f'{gitlab_url}/projects/{project_id}/repository/branches', headers=headers, json=data)
    return response.json()

def protect_branch(project_id, branch_name):
    data = {
        'name': branch_name,
        'push_access_level': 0,
        'merge_access_level': 0
    }
    response = requests.post(f'{gitlab_url}/projects/{project_id}/protected_branches', headers=headers, json=data)
    return response.json()

def set_default_branch(project_id, branch_name):
    data = {
        'default_branch': branch_name
    }
    response = requests.put(f'{gitlab_url}/projects/{project_id}', headers=headers, json=data)
    return response.json()

def delete_branch(project_id, branch_name):
    response = requests.delete(f'{gitlab_url}/projects/{project_id}/repository/branches/{branch_name}', headers=headers)
    return response.status_code

def create_nested_subgroups_and_project(full_path, project_name):
    parts = full_path.split('/')
    parent_id = None
    actions_taken = False
    
    for part in parts:
        group_path = '/'.join(parts[:parts.index(part) + 1])
        group_id = get_group_id(group_path)
        
        if not group_id:
            group_info = create_group(part, parent_id)
            parent_id = group_info['id']
            print(f"Created group: {group_path}")
            actions_taken = True
        else:
            parent_id = group_id
            print(f"Group already exists: {group_path}")
    
    # Check if the project exists
    project_id = get_project_id(project_name, parent_id)
    
    if not project_id:
        # Create the project in the final subgroup
        project = create_project(project_name, parent_id)
        project_id = project['id']
        print(f"Created project: {project_name}")
        actions_taken = True
    else:
        project = {'id': project_id, 'name': project_name, 'web_url': f'{gitlab_url}/{full_path}/{project_name}'}
        print(f"Project already exists: {project_name}")

    # Create branches if they don't exist
    branches = ['develop', 'test', 'prod']
    for branch in branches:
        if not get_branch(project_id, branch):
            create_branch(project_id, branch)
            print(f"Created branch: {branch}")
            actions_taken = True
        else:
            print(f"Branch already exists: {branch}")

    # Protect branches
    for branch in ['test', 'prod']:
        if get_branch(project_id, branch):
            protect_branch(project_id, branch)
            print(f"Protected branch: {branch}")

    # Set default branch
    set_default_branch(project_id, 'develop')
    print("Set 'develop' as the default branch")

    # Delete main branch if it exists
    if get_branch(project_id, 'main'):
        delete_branch(project_id, 'main')
        print("Deleted 'main' branch")
        actions_taken = True

    if not actions_taken:
        print("No actions taken as all criteria were met")

    return project

# Example usage
full_group_path = 'chris-devops/production/non-gxp/poc'
project_name = 'my_project'

created_project = create_nested_subgroups_and_project(full_group_path, project_name)
print(f"Project created: {created_project['name']} at {created_project['web_url']}")
