import re

def parse_schema(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    models_code = [
        "import uuid",
        "from datetime import datetime",
        "from sqlalchemy import Column, String, Integer, BigInteger, Text, Boolean, Numeric, TIMESTAMP, ForeignKey",
        "from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY",
        "from sqlalchemy.orm import relationship",
        "from app.db.database import Base",
        "\n"
    ]
    
    current_table = None
    table_dict = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith("TABLE:"):
            current_table = line.split("TABLE: ")[1]
            table_dict[current_table] = {"columns": [], "pk": [], "fk": []}
        elif line.startswith("- PK:"):
            pk_str = line.split("- PK: ")[1]
            pks = eval(pk_str)
            table_dict[current_table]["pk"] = pks
        elif line.startswith("- FK:"):
            fk_str = line.split("- FK: ")[1]
            # e.g. ['application_id'] -> applications.['id']
            match = re.search(r"\['(.*?)'\] -> (.*?)\.\['(.*?)'\]", fk_str)
            if match:
                col = match.group(1)
                ref_table = match.group(2)
                ref_col = match.group(3)
                table_dict[current_table]["fk"].append((col, ref_table, ref_col))
        elif line.startswith("- "):
            # Column
            col_str = line[2:]
            parts = col_str.split(" (Nullable: ")
            if len(parts) == 2:
                name_type = parts[0].split(": ")
                col_name = name_type[0]
                col_type = name_type[1]
                nullable = parts[1].replace(")", "") == "True"
                table_dict[current_table]["columns"].append((col_name, col_type, nullable))
                
    for table_name, data in table_dict.items():
        class_name = "".join([word.capitalize() for word in table_name.split("_")])
        if class_name.endswith("s"):
            class_name = class_name[:-1]
        if class_name == "FailureMemorie":
            class_name = "FailureMemory"
        if class_name == "Repositorie":
            class_name = "Repository"
            
        models_code.append(f"class {class_name}(Base):")
        models_code.append(f"    __tablename__ = '{table_name}'\n")
        
        for col_name, col_type, nullable in data["columns"]:
            primary_key = "primary_key=True" if col_name in data["pk"] else ""
            nullable_str = f"nullable={nullable}"
            
            # Type mapping
            if col_type.startswith("VARCHAR"):
                length = col_type.split("(")[1].replace(")", "")
                mapped_type = f"String({length})"
            elif col_type == "TEXT":
                mapped_type = "Text"
            elif col_type == "UUID":
                mapped_type = "UUID(as_uuid=True)"
            elif col_type == "TIMESTAMP":
                mapped_type = "TIMESTAMP"
            elif col_type == "BIGINT":
                mapped_type = "BigInteger"
            elif col_type == "INTEGER":
                mapped_type = "Integer"
            elif col_type.startswith("NUMERIC"):
                mapped_type = col_type
            elif col_type == "JSONB":
                mapped_type = "JSONB"
            elif col_type == "BOOLEAN":
                mapped_type = "Boolean"
            elif col_type == "ARRAY":
                mapped_type = "ARRAY(String)" # default to string array
            else:
                mapped_type = "String"
                
            fk_str = ""
            for fk in data["fk"]:
                if fk[0] == col_name:
                    fk_str = f"ForeignKey('{fk[1]}.{fk[2]}'), "
            
            args = [mapped_type]
            if fk_str:
                args.append(fk_str.strip(", "))
            if primary_key:
                args.append(primary_key)
            args.append(nullable_str)
            
            models_code.append(f"    {col_name} = Column({', '.join(args)})")
            
        models_code.append("\n")

    with open("D:/CodeGuardian/backend/app/db/models.py", "w") as f:
        f.write("\n".join(models_code))
        
parse_schema("D:/CodeGuardian/schema.txt")
print("Models generated")
