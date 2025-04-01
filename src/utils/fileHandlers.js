import Papa from 'papaparse';
import * as XLSX from 'xlsx';

/**
 * Process a file (CSV or Excel) and return the structured data
 * @param {File} file - The file object to process
 * @returns {Promise<Array>} - The structured data from the file
 */
export const processFile = async (file) => {
  if (!file) {
    throw new Error('No file provided');
  }

  try {
    if (file.name.endsWith('.csv')) {
      return await processCSV(file);
    } else if (file.name.match(/\.xlsx?$/)) {
      return await processExcel(file);
    } else {
      throw new Error('Unsupported file type. Please upload a CSV or Excel file.');
    }
  } catch (error) {
    console.error('Error processing file:', error);
    throw error;
  }
};

/**
 * Process a CSV file and return the data
 * @param {File} file - The CSV file
 * @returns {Promise<Array>} - Parsed CSV data
 */
const processCSV = async (file) => {
  const text = await file.text();
  
  return new Promise((resolve, reject) => {
    Papa.parse(text, {
      header: true,
      skipEmptyLines: true,
      transformHeader: header => header.trim(),
      complete: (results) => {
        // Validate required columns (example)
        if (!validateCitationData(results.data)) {
          reject(new Error('CSV file is missing required columns (title and/or abstract)'));
          return;
        }
        
        // Add IDs if not present
        const data = results.data.map((row, index) => ({
          id: row.id || `citation-${index}`,
          ...row
        }));
        
        resolve(data);
      },
      error: (error) => {
        reject(new Error(`CSV parsing error: ${error.message}`));
      }
    });
  });
};

/**
 * Process an Excel file and return the data
 * @param {File} file - The Excel file
 * @returns {Promise<Array>} - Parsed Excel data
 */
const processExcel = async (file) => {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: 'array' });
  
  // Get the first worksheet
  const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
  const data = XLSX.utils.sheet_to_json(firstSheet);
  
  // Validate required columns (example)
  if (!validateCitationData(data)) {
    throw new Error('Excel file is missing required columns (title and/or abstract)');
  }
  
  // Add IDs if not present
  return data.map((row, index) => ({
    id: row.id || `citation-${index}`,
    ...row
  }));
};

/**
 * Validate that the citation data has the required columns
 * @param {Array} data - The data to validate
 * @returns {boolean} - Whether the data is valid
 */
const validateCitationData = (data) => {
  if (!data || data.length === 0) {
    return false;
  }
  
  // Check for required columns in the first row
  const firstRow = data[0];
  const hasTitle = 'title' in firstRow || 'Title' in firstRow;
  const hasAbstract = 'abstract' in firstRow || 'Abstract' in firstRow;
  
  return hasTitle && hasAbstract;
};

/**
 * Convert data to CSV and trigger a download
 * @param {Array} data - The data to convert to CSV
 * @param {string} filename - The name of the file to download
 */
export const downloadCSV = (data, filename = 'download.csv') => {
  if (!data || data.length === 0) {
    console.error('No data to download');
    return;
  }
  
  const csv = Papa.unparse(data);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Convert data to Excel and trigger a download
 * @param {Array} data - The data to convert to Excel
 * @param {string} filename - The name of the file to download
 */
export const downloadExcel = (data, filename = 'download.xlsx') => {
  if (!data || data.length === 0) {
    console.error('No data to download');
    return;
  }
  
  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Results');
  
  XLSX.writeFile(workbook, filename);
};