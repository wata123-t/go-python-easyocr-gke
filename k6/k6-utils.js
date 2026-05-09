// k6-utils.js (v1.4.0)
export function randomIntBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

export function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

export function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    let r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function findBetween(content, left, right) {
  let start = content.indexOf(left);
  if (start === -1) return '';
  start += left.length;
  let end = content.indexOf(right, start);
  if (end === -1) return '';
  return content.substring(start, end);
}
