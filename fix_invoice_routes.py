#!/usr/bin/env python3

# Script to remove owner references from invoice_routes.py

with open('/home/muntazir/work/projects/ai-pres/ai-pres-be/app/routes/invoice_routes.py', 'r') as file:
    content = file.read()

# Replace the problematic pattern in all routes
content = content.replace('response.owner = UserMinimumResponse.model_validate(owner_user)', '')
content = content.replace('# Add tenant and owner information', '# Add tenant information')
content = content.replace('# Get property owner information', '# No need to get property owner information')
content = content.replace('property_obj = db.query(Property).filter(Property.id == booking.property_id).first()\n        if property_obj and property_obj.owner_id:\n            owner_user = db.query(User).filter(User.id == property_obj.owner_id).first()\n            if owner_user:', '')
content = content.replace('# Prepare response with tenant and owner information', '# Prepare response with tenant information')

with open('/home/muntazir/work/projects/ai-pres/ai-pres-be/app/routes/invoice_routes.py', 'w') as file:
    file.write(content)

print("Successfully removed owner references from invoice_routes.py")
