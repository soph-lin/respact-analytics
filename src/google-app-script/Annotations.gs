function convertAnnotationsToJSON() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const file = DriveApp.getFileById(ss.getId());
  const parentFolder = file.getParents().next();

  // Get friction labels
  const labelStartCol = 11; // Column L (0-indexed)
  const labelEndCol = 22; // Column W
  const labelColumns = Array.from(
    { length: labelEndCol - labelStartCol + 1 },
    (_, i) => labelStartCol + i
  );

  const versions = ["v1", "v2"];

  versions.forEach((version) => {
    const sheet = ss.getSheetByName(version);
    const data = sheet.getDataRange().getValues();
    const headers = data[0];

    const labelNames = labelColumns.map((i) => headers[i]);

    const groupedData = {};

    for (let i = 1; i < data.length; i++) {
      const row = data[i];
      const folder = row[0];
      const filename = row[1];
      const line = row[2];

      if (!folder || !filename || !line) continue;

      const key = `${folder}|||${filename}|||${line}`;
      if (groupedData[key]) continue; // skip duplicate

      const labels = {};
      labelColumns.forEach((colIdx, j) => {
        labels[labelNames[j]] = row[colIdx] ? 1 : 0;
      });

      const jsonRow = {
        filename,
        line,
        labels,
      };

      if (!groupedData[folder]) groupedData[folder] = [];
      groupedData[folder].push(jsonRow);

      groupedData[key] = true; // mark as seen
    }

    Object.keys(groupedData).forEach((folder) => {
      if (folder.includes("|||")) return; // skip dup keys

      const jsonContent = JSON.stringify(groupedData[folder], null, 2);
      const blob = Utilities.newBlob(
        jsonContent,
        "application/json",
        `${folder}.${version}.json`
      );
      parentFolder.createFile(blob);
    });
  });
}

function compareAnnotations() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet1 = ss.getSheetByName("v1");
  const sheet2 = ss.getSheetByName("v2");
  let sheet3 = ss.getSheetByName("Comparison");
  if (!sheet3) sheet3 = ss.insertSheet("Comparison");
  else sheet3.clear();

  const data1 = sheet1.getDataRange().getValues();
  const data2 = sheet2.getDataRange().getValues();
  const headers = data1[0];

  // Column indexes to compare (D–I = 3–8, L–W = 11–22) - 0-indexed
  const compareIndexes = [...Array(6).keys()]
    .map((i) => i + 3)
    .concat([...Array(12).keys()].map((i) => i + 11));

  const result = [[headers[0], headers[1], headers[2], "Differences"]];

  const maxRows = Math.max(data1.length, data2.length);

  for (let i = 1; i < maxRows; i++) {
    const row1 = data1[i] || [];
    const row2 = data2[i] || [];

    const diffs = compareIndexes
      .filter((colIdx) => (row1[colIdx] || "") !== (row2[colIdx] || ""))
      .map((colIdx) => headers[colIdx]);

    if (diffs.length > 0) {
      result.push([
        row1[0] || row2[0] || "", // Col A
        row1[1] || row2[1] || "", // Col B
        row1[2] || row2[2] || "", // Col C
        diffs.join(", "),
      ]);
    }
  }

  sheet3.getRange(1, 1, result.length, result[0].length).setValues(result);
}
