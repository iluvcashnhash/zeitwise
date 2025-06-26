import { Client } from 'pg';
import fs from 'fs';
import path from 'path';

// Database connection configuration
const dbConfig = {
  host: '127.0.0.1',
  port: 54322,
  user: 'postgres',
  password: 'postgres',
  database: 'postgres',
};

// Type mappings from PostgreSQL to TypeScript
const typeMap: Record<string, string> = {
  // Numeric types
  'smallint': 'number',
  'integer': 'number',
  'bigint': 'number',
  'decimal': 'number',
  'numeric': 'number',
  'real': 'number',
  'double precision': 'number',
  'smallserial': 'number',
  'serial': 'number',
  'bigserial': 'number',
  
  // Character types
  'character varying': 'string',
  'varchar': 'string',
  'character': 'string',
  'char': 'string',
  'text': 'string',
  
  // Binary data
  'bytea': 'string',
  
  // Date/Time types
  'timestamp with time zone': 'string',
  'timestamp without time zone': 'string',
  'timestamp': 'string',
  'date': 'string',
  'time with time zone': 'string',
  'time without time zone': 'string',
  'time': 'string',
  'interval': 'string',
  
  // Boolean
  'boolean': 'boolean',
  'bool': 'boolean',
  
  // JSON
  'json': 'Json',
  'jsonb': 'Json',
  
  // UUID
  'uuid': 'string',
  
  // Network address types
  'inet': 'string',
  'cidr': 'string',
  'macaddr': 'string',
  'macaddr8': 'string',
  
  // Bit string types
  'bit': 'string',
  'bit varying': 'string',
  'varbit': 'string',
};

// Custom enum mappings
const enumMap: Record<string, string> = {
  'message_role': "'user' | 'assistant' | 'system'",
  'content_type': "'text' | 'image' | 'video' | 'link'",
  'source_type': "'telegram' | 'web' | 'api' | 'manual'"
};

async function generateTypes() {
  const client = new Client(dbConfig);
  
  try {
    await client.connect();
    
    // Get all tables in the public schema
    const tablesQuery = `
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
      ORDER BY table_name;
    `;
    
    const { rows: tables } = await client.query(tablesQuery);
    
    if (tables.length === 0) {
      console.log('No tables found in the public schema');
      return;
    }
    
    // Start generating TypeScript types
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
    for (const { table_name } of tables) {
      console.log(`Processing table: ${table_name}`);
      
      // Get table columns
      const columnsQuery = `
        SELECT 
          column_name,
          data_type,
          udt_name,
          is_nullable,
          column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = $1
        ORDER BY ordinal_position;
      `;
      
      const { rows: columns } = await client.query(columnsQuery, [table_name]);
      
      if (!columns || columns.length === 0) {
        console.log(`No columns found for table ${table_name}`);
        continue;
      }
      
      // Add table type
      types += `      ${table_name}: {\n        Row: {\n`;

      // Add column types for Row
      for (const column of columns) {
        const { column_name, data_type, udt_name, is_nullable } = column;
        const isOptional = is_nullable === 'YES' ? '?' : '';
        
        // Check if this is a custom enum type
        let tsType = enumMap[udt_name] || typeMap[data_type] || 'any';
        
        // Special handling for arrays
        if (data_type === 'ARRAY') {
          tsType = 'any[]';
        }
        
        types += `          ${column_name}${isOptional}: ${tsType};\n`;
      }
      
      // Close Row type
      types += `        };\n`;
      
      // Add Insert type (same as Row but with optional fields)
      types += `        Insert: {\n`;
      for (const column of columns) {
        const { column_name, data_type, udt_name, column_default } = column;
        
        // Skip identity/serial columns for inserts
        if (column_default && column_default.includes('nextval')) continue;
        
        // Check if this is a custom enum type
        let tsType = enumMap[udt_name] || typeMap[data_type] || 'any';
        
        // Special handling for arrays
        if (data_type === 'ARRAY') {
          tsType = 'any[]';
        }
        
        // Check if column is required for insert (NOT NULL and no default)
        const isRequired = column.is_nullable === 'NO' && !column_default;
        types += `          ${column_name}${isRequired ? '' : '?'}: ${tsType};\n`;
      }
      
      // Close Insert type
      types += `        };\n`;
      
      // Add Update type (all fields optional)
      types += `        Update: {\n`;
      for (const column of columns) {
        // Skip primary key for updates
        if (column.column_name === 'id') continue;
        
        const { column_name, data_type, udt_name } = column;
        
        // Check if this is a custom enum type
        let tsType = enumMap[udt_name] || typeMap[data_type] || 'any';
        
        // Special handling for arrays
        if (data_type === 'ARRAY') {
          tsType = 'any[]';
        }
        
        types += `          ${column_name}?: ${tsType} | null;\n`;
      }
      
      // Close Update type and table type
      types += `        };\n      };\n`;
    }
    
    // Close the Database type
    types += `    };\n  };\n};\n\n`;
    
    // Add helper type
    types += `// This type is used to type the Supabase client\n`;
    types += `export type Tables<T extends keyof Database['public']['Tables']> = Database['public']['Tables'][T]['Row'];\n`;
    
    // Write the types to a file
    const outputPath = path.join(process.cwd(), 'types', 'database.types.ts');
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, types);
    
    console.log(`✅ Successfully generated database types at ${outputPath}`);
  } catch (error) {
    console.error('Error generating types:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

// Run the type generation
generateTypes().catch(console.error);
