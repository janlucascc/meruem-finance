fetch("http://127.0.0.1:5000/saldo")
  .then(res => res.json())
  .then(data => {
    document.getElementById("saldo").innerText = "R$ " + data.saldo;
  });