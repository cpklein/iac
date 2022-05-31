# iac
Scripts to deal with Integration as Code specification

Conversor Postman → .iac
O grupo de Professional Services desenvolveu um script que transforma as collections em .iac. 

Você pode acessar esse script através de uma chamada REST.

*Variáveis
Todas as varáveis encontradas no request da collection são convertidas em parâmetros do .iac.

Entretanto é comum encontrar nas collections variáveis que não desejamos, tais como {{server}} que descrevem o endereço do servidor. Nesse caso podemos usar a lista change_variables para removê-las. Basta especificar um nome vazio "“ para isso.

*Response
As collections permitem armazenar as respostas esperadas das APIs. Nesse momento não estamos utilizando essa informação no .iac. Para remover a response do .iac, especifique  "include_response" : false

*Path 
O PATH do .iac está decomposto em uma lista com seus ramos. Nas collections podemos já encontrar esse formato e portanto preservamos, ou podemos encontrar apenas o formato raw e nesse caso fazemos um parse  e incluímos o a lista do path.

Variáveis especificadas no path através de “:” também são inseridas nos parâmetros

*Header
Todas os parâmetros da collection que constam no header são convertidos em parâmetros do .iac. Caso deseje remover algum parâmetro, especifique-o na lista remove_header.

*Collection
Envie toda a collection  no parâmetro collection. 

