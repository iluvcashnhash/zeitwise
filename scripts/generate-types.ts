import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import path from 'path';

// Configuration
const supabaseUrl = 'http://127.0.0.1:54321';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

async function generateTypes() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get all tables in the public schema
    const { data: tables, error: tablesError } = await supabase
      .rpc('get_tables')
      .select();

    if (tablesError) throw tablesError;
    if (!tables) {
      console.log('No tables found in the public schema');
      return;
    }

    // Generate TypeScript types
    let types = `// Auto-generated TypeScript types from database schema
// Generated at: ${new Date().toISOString()}

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
`;

    // Process each table
    for (const table of tables) {
      const tableName = table.table_name;
      
      // Get table columns
      const { data: columns, error: columnsError } = await supabase
        .rpc('get_columns', { table_name: tableName })
        .select();

      if (columnsError) {
        console.error(`Error getting columns for table ${tableName}:`, columnsError);
        continue;
      }

      if (!columns || columns.length === 0) {
        console.log(`No columns found for table ${tableName}`);
        continue;
      }

      // Add table type
      types += `      ${tableName}: {
        Row: {
`;

      // Add column types
      for (const column of columns) {
        const columnName = column.column_name;
        const isNullable = column.is_nullable === 'YES';
        const hasDefault = column.column_default !== null;
        const isOptional = isNullable || hasDefault ? '?' : '';
        
        // Map PostgreSQL types to TypeScript types
        let tsType = 'unknown';
        switch (column.data_type) {
          case 'uuid':
          case 'text':
          case 'character varying':
          case 'character':
          case 'varchar':
            tsType = 'string';
            break;
          case 'integer':
          case 'bigint':
          case 'decimal':
          case 'numeric':
          case 'real':
          case 'double precision':
          case 'smallint':
          case 'serial':
          case 'bigserial':
            tsType = 'number';
            break;
          case 'boolean':
            tsType = 'boolean';
            break;
          case 'jsonb':
          case 'json':
            tsType = 'Json';
            break;
          case 'timestamp with time zone':
          case 'timestamp without time zone':
          case 'date':
          case 'time':
          case 'timetz':
          case 'timestamptz':
            tsType = 'string'; // or Date if you prefer
            break;
          case 'ARRAY':
            tsType = 'any[]';
            break;
          case 'USER-DEFINED':
            // Handle enums
            if (column.udt_name === 'message_role') {
              tsType = "'user' | 'assistant' | 'system'";
            } else if (column.udt_name === 'content_type') {
              tsType = "'text' | 'image' | 'video' | 'link'";
            } else if (column.udt_name === 'source_type') {
              tsType = "'telegram' | 'web' | 'api' | 'manual'";
            } else {
              tsType = 'any';
              console.warn(`Unknown user-defined type ${column.udt_name} for column ${tableName}.${columnName}`);
            }
            break;
          default:
            tsType = 'any';
            console.warn(`Unknown type ${column.data_type} for column ${tableName}.${columnName}`);
        }

        types += `          ${columnName}${isOptional}: ${tsType};
`;
      }

      // Close the Row type
      types += `        };
`;

      // Add Insert type (same as Row but with optional fields)
      types += `        Insert: {
`;
      for (const column of columns) {
        const columnName = column.column_name;
        // Skip identity/serial columns for inserts
        if (column.column_default?.includes('nextval')) continue;
        
        // Same type mapping as above
        let tsType = 'unknown';
        switch (column.data_type) {
          case 'uuid':
          case 'text':
          case 'character varying':
          case 'character':
          case 'varchar':
            tsType = 'string';
            break;
          case 'integer':
          case 'bigint':
          case 'decimal':
          case 'numeric':
          case 'real':
          case 'double precision':
          case 'smallint':
          case 'serial':
          case 'bigserial':
            tsType = 'number';
            break;
          case 'boolean':
            tsType = 'boolean';
            break;
          case 'jsonb':
          case 'json':
            tsType = 'Json';
            break;
          case 'timestamp with time zone':
          case 'timestamp without time zone':
          case 'date':
          case 'time':
          case 'timetz':
          case 'timestamptz':
            tsType = 'string';
            break;
          case 'ARRAY':
            tsType = 'any[]';
            break;
          case 'USER-DEFINED':
            // Handle enums
            if (column.udt_name === 'message_role') {
              tsType = "'user' | 'assistant' | 'system'";
            } else if (column.udt_name === 'content_type') {
              tsType = "'text' | 'image' | 'video' | 'link'";
            } else if (column.udt_name === 'source_type') {
              tsType = "'telegram' | 'web' | 'api' | 'manual'";
            } else {
              tsType = 'any';
            }
            break;
          default:
            tsType = 'any';
        }

        // All fields are optional for inserts (except those with NOT NULL and no default)
        const isRequired = column.is_nullable === 'NO' && !column.column_default;
        types += `          ${columnName}${isRequired ? '' : '?'}: ${tsType};
`;
      }

      // Close the Insert type
      types += `        };
`;

      // Add Update type (all fields optional)
      types += `        Update: {
`;
      for (const column of columns) {
        const columnName = column.column_name;
        // Skip primary key for updates
        if (columnName === 'id') continue;
        
        // Same type mapping as above
        let tsType = 'unknown';
        switch (column.data_type) {
          case 'uuid':
          case 'text':
          case 'character varying':
          case 'character':
          case 'varchar':
            tsType = 'string';
            break;
          case 'integer':
          case 'bigint':
          case 'decimal':
          case 'numeric':
          case 'real':
          case 'double precision':
          case 'smallint':
          case 'serial':
          case 'bigserial':
            tsType = 'number';
            break;
          case 'boolean':
            tsType = 'boolean';
            break;
          case 'jsonb':
          case 'json':
            tsType = 'Json';
            break;
          case 'timestamp with time zone':
          case 'timestamp without time zone':
          case 'date':
          case 'time':
          case 'timetz':
          case 'timestamptz':
            tsType = 'string';
            break;
          case 'ARRAY':
            tsType = 'any[]';
            break;
          case 'USER-DEFINED':
            // Handle enums
            if (column.udt_name === 'message_role') {
              tsType = "'user' | 'assistant' | 'system'";
            } else if (column.udt_name === 'content_type') {
              tsType = "'text' | 'image' | 'video' | 'link'";
            } else if (column.udt_name === 'source_type') {
              tsType = "'telegram' | 'web' | 'api' | 'manual'";
            } else {
              tsType = 'any';
            }
            break;
          default:
            tsType = 'any';
        }

        types += `          ${columnName}?: ${tsType} | null;
`;
      }

      // Close the Update type and table type
      types += `        };
      };
`;
    }

    // Close the Database type
    types += `    };
  };
};

// This type is used to type the Supabase client
export type Tables<T extends keyof Database['public']['Tables']> = Database['public']['Tables'][T]['Row'];
`;

    // Write the types to a file
    const outputPath = path.join(process.cwd(), 'types', 'database.types.ts');
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, types);

    console.log(`✅ Successfully generated database types at ${outputPath}`);
  } catch (error) {
    console.error('Error generating types:', error);
    process.exit(1);
  }
}

// Create the required SQL functions
async function setupSqlFunctions() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    // Create a function to get all tables in the public schema
    const { error: tablesFnError } = await supabase.rpc('create_or_replace_function', {
      function_name: 'get_tables',
      function_definition: `
        CREATE OR REPLACE FUNCTION get_tables()
        RETURNS TABLE (table_name text) AS $$
        BEGIN
          RETURN QUERY
          SELECT tablename::text
          FROM pg_tables
          WHERE schemaname = 'public';
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
      `
    });

    if (tablesFnError) throw tablesFnError;

    // Create a function to get columns for a table
    const { error: columnsFnError } = await supabase.rpc('create_or_replace_function', {
      function_name: 'get_columns',
      function_definition: `
        CREATE OR REPLACE FUNCTION get_columns(table_name text)
        RETURNS TABLE (
          column_name text,
          data_type text,
          is_nullable text,
          column_default text,
          udt_name text
        ) AS $$
        BEGIN
          RETURN QUERY
          SELECT 
            a.attname::text as column_name,
            pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
            CASE 
              WHEN a.attnotnull THEN 'NO'
              ELSE 'YES'
            END as is_nullable,
            pg_catalog.pg_get_expr(adef.adbin, adef.adrelid) as column_default,
            t.typname as udt_name
          FROM pg_catalog.pg_attribute a
          LEFT JOIN pg_catalog.pg_attrdef adef ON a.attrelid = adef.adrelid AND a.attnum = adef.adnum
          JOIN pg_catalog.pg_type t ON a.atttypid = t.oid
          WHERE a.attrelid = ('public.' || $1)::regclass
          AND a.attnum > 0
          AND NOT a.attisdropped
          ORDER BY a.attnum;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
      `
    });

    if (columnsFnError) throw columnsFnError;

    console.log('✅ Successfully set up SQL functions');
  } catch (error) {
    console.error('Error setting up SQL functions:', error);
    process.exit(1);
  }
}

// Run the setup and generation
async function main() {
  console.log('Setting up SQL functions...');
  await setupSqlFunctions();
  
  console.log('Generating TypeScript types...');
  await generateTypes();
}

main().catch(console.error);
