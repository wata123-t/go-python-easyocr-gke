import http from 'k6/http';
import { check, sleep } from 'k6';
//import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { uuidv4 } from './k6-utils.js';


// 1. Pythonが作った正解リスト(JSON)を読み込む
const mapping = JSON.parse(open('./test_images/mapping.json'));
const imageFiles = [];

// 2. 100枚の画像をメモリに読み込む
for (let i = 1; i <= 100; i++) {
  const filename = `${String(i).padStart(3, '0')}.png`;
  
  imageFiles.push({
    name: filename,
    expected: mapping[filename], // JSONから正解を取得
    bin: open(`./test_images/${filename}`, 'b')
  });
}


export default function () {
  const url = 'http://35.221.115.130:8080/predict';
  
  // ★ 4. 順番に1枚選ぶ (0, 1, 2... 99, 0, 1...)
  // execution.instance.iterationInTest を使う方法もありますが、簡易的には __ITER を使用します
  const index = __ITER % imageFiles.length; 
  const targetImage = imageFiles[index];

  const data = {
    image: http.file(targetImage.bin, targetImage.name, 'image/png'),
  };

  const k6SendTime = Date.now();

  const params = {
    headers: {
      'X-Correlation-ID': uuidv4(),
      'X-Expected-Text': targetImage.expected,
      'X-K6-Send-Time': k6SendTime.toString(),
      'X-Image-Index': index.toString(), // デバッグ用に何番目か送るのもアリ
    },
  };

  const res = http.post(url, data, params);

  // （以下、check処理はそのまま）
  check(res, {
    'Status is 200': (r) => r.status === 200,
    'OCR Content Match': (r) => {
      try {
        const body = r.json();
        const match = body.result.includes(targetImage.expected);
        // ★ 失敗した時にログを出すと特定が捗ります
        if (!match) {
           console.log(`Failed! Index: ${index}, File: ${targetImage.name}, Expected: ${targetImage.expected}, Got: ${body.result}`);
        }
        return match;
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1); // 待機時間
//  sleep(2); // 待機時間
}
