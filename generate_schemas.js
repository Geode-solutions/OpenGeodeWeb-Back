const fs = require("fs");
const path = require("path");
const glob = require("glob");

const directoryPath = path.join(__dirname, "src/opengeodeweb_back");

function return_json_schema(directoryPath, folder_path) {
  const folders = fs
    .readdirSync(directoryPath, { withFileTypes: true })
    .filter((folder) => folder.isDirectory())
    .map((folder) => ({
      name: folder.name,
      path: path.join(directoryPath, folder.name),
    }));
  var folders_schemas = {};
  folders.forEach((folder) => {
    if (folder.name == "schemas") {
      const jsonFiles = glob.sync(path.join(folder.path, "**/*.json"));
      var schemas = {};
      jsonFiles.forEach((filePath) => {
        try {
          const fileContent = fs.readFileSync(filePath, "utf8");
          var jsonData = JSON.parse(fileContent);
          var filename = filePath.replace(/^.*[\\/]/, "").replace(".json", "");
          var route = jsonData["route"];
          jsonData["$id"] = folder_path + route;
          schemas[filename] = jsonData;
        } catch (error) {
          console.error(
            `Erreur lors de la lecture du fichier ${filePath}:`,
            error
          );
        }
      });
      folders_schemas = Object.keys(schemas).reduce((acc, key) => {
        const currentSchema = schemas[key];
        const modifiedSchema = { $id: currentSchema["$id"], ...currentSchema };
        acc[key] = modifiedSchema;
        return acc;
      }, folders_schemas);
    } else {
      var new_folder_path = folder_path + "/" + folder.name;
      var test = return_json_schema(folder.path, new_folder_path);
      folders_schemas[folder.name] = test;
    }
  });
  return folders_schemas;
}

const jsonDataStructure = return_json_schema(directoryPath, "ogw_back");
console.log("jsonDataStructure", jsonDataStructure);
const outputFile = path.join(directoryPath, "schemas.json");
fs.writeFileSync(outputFile, JSON.stringify(jsonDataStructure, null, 2));

console.log("Fichier JSON créé avec succès :", outputFile);
