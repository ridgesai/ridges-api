
from db.operations_new import DatabaseManager

db_manager = DatabaseManager()
codegen_challenges = db_manager.get_codegen_challenges()
print("All codegen challenges:")
for challenge in codegen_challenges:
    print(challenge)
db_manager.close()