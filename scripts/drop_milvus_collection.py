from pymilvus import connections, utility

# Connect to Milvus
connections.connect(alias="default", host="localhost", port="19530")

# Collection name you want to drop
collection_name = "documents"

# Drop it
if utility.has_collection(collection_name):
    utility.drop_collection(collection_name)
    print(f"✅ Dropped collection: {collection_name}")
else:
    print(f"ℹ️ Collection '{collection_name}' does not exist.")
