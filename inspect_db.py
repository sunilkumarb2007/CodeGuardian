import sqlalchemy
from sqlalchemy import create_engine, inspect

# Assuming default local postgres credentials
engine = create_engine('postgresql://postgres:postgres@localhost/codeguardian_db')

inspector = inspect(engine)
tables = inspector.get_table_names()

output = []
output.append(f"Found {len(tables)} tables: {tables}\n")

for table in tables:
    output.append(f"\nTABLE: {table}")
    columns = inspector.get_columns(table)
    for col in columns:
        output.append(f"  - {col['name']}: {col['type']} (Nullable: {col['nullable']})")
    
    pks = inspector.get_pk_constraint(table)
    if pks and pks['constrained_columns']:
        output.append(f"  - PK: {pks['constrained_columns']}")
        
    fks = inspector.get_foreign_keys(table)
    for fk in fks:
        output.append(f"  - FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

with open("D:/CodeGuardian/schema.txt", "w") as f:
    f.write("\n".join(output))

print("Schema written to D:/CodeGuardian/schema.txt")
