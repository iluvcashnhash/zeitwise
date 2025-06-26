import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import path from 'path';

// This script generates TypeScript types from the database schema
// Run with: npx tsx scripts/generate-db-types.ts

async function generateTypes() {
  // Use the local Supabase URL and anon key from the running instance
  const supabaseUrl = 'http://127.0.0.1:54321';
  const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';
  
  const supabase = createClient(supabaseUrl, supabaseKey);

  try {
    // Get the database schema
    const { data: tables, error } = await supabase
      .from('pg_tables')
      .select('tablename')
      .eq('schemaname', 'public');

    if (error) {
      throw error;
    }

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

    // Add table types
    for (const table of tables) {
      const tableName = table.tablename;
      
      // Get table columns
      const { data: columns, error: columnError } = await supabase
        .from('information_schema.columns')
        .select('column_name, data_type, is_nullable, column_default')
        .eq('table_schema', 'public')
        .eq('table_name', tableName)
        .order('ordinal_position');

      if (columnError) {
        console.error(`Error getting columns for table ${tableName}:`, columnError);
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
        let tsType = 'unknown';
        
        // Map PostgreSQL types to TypeScript types
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
            tsType = 'string'; // or Date if you prefer
            break;
          case 'ARRAY':
            tsType = 'any[]';
            break;
          default:
            tsType = 'any';
            console.warn(`Unknown type ${column.data_type} for column ${tableName}.${columnName}`);
        }

        const isOptional = column.is_nullable === 'YES' ? '?' : '';
        types += `          ${column.name}${isOptional}: ${tsType};
`;
      }

      types += `        };
        Insert: {
`;

      // Add insert types (all fields optional except required ones)
      for (const column of columns) {
        const columnName = column.column_name;
        let tsType = 'unknown';
        
        // Same type mapping as above
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
            tsType = 'string';
            break;
          case 'ARRAY':
            tsType = 'any[]';
            break;
          default:
            tsType = 'any';
        }

        // Check if column has a default value or is auto-generated
        const hasDefault = column.column_default !== null || 
                          ['uuid_generate_v4()', 'now()'].includes(column.column_default || '');
        
        const isOptional = column.is_nullable === 'YES' || hasDefault ? '?' : '';
        types += `          ${column.name}${isOptional}: ${tsType};
`;
      }

      types += `        };
        Update: {
`;

      // Add update types (all fields optional)
      for (const column of columns) {
        const columnName = column.column_name;
        let tsType = 'unknown';
        
        // Skip primary key for updates
        if (columnName === 'id') continue;
        
        // Same type mapping as above
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
            tsType = 'string';
            break;
          case 'ARRAY':
            tsType = 'any[]';
            break;
          default:
            tsType = 'any';
        }

        types += `          ${column.name}?: ${tsType} | null;
`;
      }

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

generateTypes();
