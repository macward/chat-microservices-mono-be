// MongoDB initialization script for development
print('Starting MongoDB initialization for conversation_service_dev...');

// Switch to the conversation service database
db = db.getSiblingDB('conversation_service_dev');

// Create collections with validation
db.createCollection('conversations', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'character_id', 'title', 'created_at'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'User ID must be a string and is required'
        },
        character_id: {
          bsonType: 'string',
          description: 'Character ID must be a string and is required'
        },
        title: {
          bsonType: 'string',
          maxLength: 200,
          description: 'Title must be a string with max 200 chars and is required'
        },
        status: {
          enum: ['active', 'archived'],
          description: 'Status can only be active or archived'
        },
        tags: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'Tags must be an array of strings'
        }
      }
    }
  }
});

// Create indexes for better performance
db.conversations.createIndex({ "user_id": 1, "created_at": -1 });
db.conversations.createIndex({ "user_id": 1, "character_id": 1 });
db.conversations.createIndex({ "user_id": 1, "status": 1 });
db.conversations.createIndex({ "user_id": 1, "tags": 1 });
db.conversations.createIndex({ "title": "text" });

print('MongoDB initialization completed successfully!');
print('Created conversation_service_dev database with:');
print('- conversations collection with validation schema');
print('- Optimized indexes for common queries');
print('- Text search index on title field');