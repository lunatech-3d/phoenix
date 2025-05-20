import sqlite3

def rebuild_resgroups_and_members(db_path='phoenix.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("\nStarting rebuild of ResGroups and ResGroupMembers...")

        # Backup current tables (optional safety step)
        cursor.execute("DROP TABLE IF EXISTS ResGroups_backup")
        cursor.execute("DROP TABLE IF EXISTS ResGroupMembers_backup")
        cursor.execute("DROP TABLE IF EXISTS Census_backup")
        cursor.execute("CREATE TABLE ResGroups_backup AS SELECT * FROM ResGroups")
        cursor.execute("CREATE TABLE ResGroupMembers_backup AS SELECT * FROM ResGroupMembers")
        cursor.execute("CREATE TABLE Census_backup AS SELECT * FROM Census")

        # Clear existing data
        cursor.execute("DELETE FROM ResGroupMembers")
        cursor.execute("DELETE FROM ResGroups")
        conn.commit()

        print("Backups created and original tables cleared.")

        # Step 1: Find all unique household identifiers from Census
        cursor.execute("""
            SELECT DISTINCT census_year, township_id, census_dwellnum, census_householdnum
            FROM Census
            WHERE census_dwellnum IS NOT NULL AND census_householdnum IS NOT NULL
        """)

        household_keys = cursor.fetchall()
        print(f"Found {len(household_keys)} unique household keys.")

        # Create new ResGroups for each key and store mapping
        resgroup_map = {}  # (year, township, dwell, hh) -> res_group_id

        for year, township_id, dwellnum, hhnum in household_keys:
            cursor.execute("""
                INSERT INTO ResGroups (res_group_year, township_id, dwelling_num, household_num, event_type, household_notes)
                VALUES (?, ?, ?, ?, 'Census', 'Rebuilt from Census Records')
            """, (year, township_id, dwellnum, hhnum))

            res_group_id = cursor.lastrowid
            resgroup_map[(year, township_id, dwellnum, hhnum)] = res_group_id

        conn.commit()
        print("ResGroups rebuilt successfully.")

        # Step 2: Update Census records with correct res_group_id
        updated_count = 0
        for key, res_group_id in resgroup_map.items():
            year, township_id, dwellnum, hhnum = key
            cursor.execute("""
                UPDATE Census
                SET res_group_id = ?
                WHERE census_year = ? AND township_id = ? AND census_dwellnum = ? AND census_householdnum = ?
            """, (res_group_id, year, township_id, dwellnum, hhnum))
            updated_count += cursor.rowcount

        conn.commit()
        print(f"Updated {updated_count} Census records with new res_group_id values.")

        # Step 3: Rebuild ResGroupMembers from Census
        cursor.execute("""
            INSERT INTO ResGroupMembers (res_group_id, res_group_member)
            SELECT res_group_id, person_id FROM Census
            WHERE res_group_id IS NOT NULL
        """)
        conn.commit()

        print("ResGroupMembers rebuilt successfully.")

        # Step 4: Verification - find mismatches or orphaned records
        print("\nRunning verification checks...")

        # Check for Census records with missing ResGroup link
        cursor.execute("""
            SELECT id FROM Census WHERE res_group_id IS NULL
        """)
        missing_links = cursor.fetchall()
        if missing_links:
            print(f"WARNING: {len(missing_links)} Census records have no res_group_id assigned.")
        else:
            print("All Census records have valid res_group_id values.")

        # Check for Census records whose person_id is not in ResGroupMembers
        cursor.execute("""
            SELECT c.id, c.person_id
            FROM Census c
            LEFT JOIN ResGroupMembers rgm ON c.res_group_id = rgm.res_group_id AND c.person_id = rgm.res_group_member
            WHERE rgm.res_group_member IS NULL
        """)
        orphaned_members = cursor.fetchall()
        if orphaned_members:
            print(f"WARNING: {len(orphaned_members)} Census records are missing from ResGroupMembers:")
            for row in orphaned_members[:10]:  # Show first 10 only
                print(f"  - Census ID {row[0]} (Person ID {row[1]})")
        else:
            print("All Census members are correctly linked in ResGroupMembers.")

        # Check for ResGroupMembers not linked to any Census record
        cursor.execute("""
            SELECT rgm.res_group_id, rgm.res_group_member
            FROM ResGroupMembers rgm
            LEFT JOIN Census c ON rgm.res_group_member = c.person_id AND rgm.res_group_id = c.res_group_id
            WHERE c.id IS NULL
        """)
        orphaned_rgm = cursor.fetchall()
        if orphaned_rgm:
            print(f"WARNING: {len(orphaned_rgm)} ResGroupMembers are not linked to any Census record:")
            for row in orphaned_rgm[:10]:
                print(f"  - ResGroup {row[0]} / Person ID {row[1]}")
        else:
            print("All ResGroupMembers are correctly linked to Census records.")

        # Check for duplicate member_order within a ResGroup
        cursor.execute("""
            SELECT res_group_id, member_order, COUNT(*)
            FROM ResGroupMembers
            WHERE member_order IS NOT NULL
            GROUP BY res_group_id, member_order
            HAVING COUNT(*) > 1
        """)
        duplicate_orders = cursor.fetchall()
        if duplicate_orders:
            print(f"WARNING: {len(duplicate_orders)} ResGroups have duplicate member_order values:")
            for row in duplicate_orders[:10]:
                print(f"  - ResGroup {row[0]} has {row[2]} members with order {row[1]}")
        else:
            print("All ResGroupMembers have unique member_order values per group (if used).")

        print("\nRebuild and verification complete.")

    except Exception as e:
        conn.rollback()
        print(f"\nError during rebuild: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    rebuild_resgroups_and_members()