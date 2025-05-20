import sqlite3
from resgroup_utils import get_or_create_resgroup

def repair_resgroup_ids(db_path="phoenix.db"):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("BEGIN")
        fixed_count = 0

        # Fetch all Census records with res_group_id assigned
        cursor.execute("""
            SELECT 
                id, 
                census_dwellnum, 
                census_householdnum, 
                census_year, 
                township_id, 
                res_group_id 
            FROM Census
            WHERE census_dwellnum IS NOT NULL 
              AND census_householdnum IS NOT NULL 
              AND census_year IS NOT NULL 
              AND township_id IS NOT NULL
        """)
        records = cursor.fetchall()

        for row in records:
            census_id = row[0]
            dwell_num = int(row[1])
            hh_num = int(row[2])
            year = int(row[3])
            township_id = int(row[4])
            old_res_group_id = row[5]

            # Get the corrected res_group_id using new logic
            new_res_group_id = get_or_create_resgroup(
                cursor,
                census_dwellnum=dwell_num,
                census_year=year,
                township_id=township_id,
                household_num=hh_num,
                event_type="Census"
            )

            # Only update if needed
            if old_res_group_id != new_res_group_id:
                cursor.execute("""
                    UPDATE Census 
                    SET res_group_id = ? 
                    WHERE id = ?
                """, (new_res_group_id, census_id))
                fixed_count += 1
                print(f"[FIXED] Census ID {census_id} → ResGroup {old_res_group_id} ➜ {new_res_group_id}")

        connection.commit()
        print(f"\n✅ Repair complete. {fixed_count} Census records were reassigned to correct ResGroups.")

    except Exception as e:
        connection.rollback()
        print("❌ Error during repair:", str(e))
    finally:
        connection.close()

if __name__ == "__main__":
    repair_resgroup_ids()
