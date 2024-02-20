import os
import requests
from bs4 import BeautifulSoup
from datetime import date

class DovizKurlari:
    
    __sonuc = {"durum" : "ERROR", "mesaj" : "Bilinmeyen hata oluştu.", "veri" : {}}
    
    # başlatıcı fonksiyon
    def __init__(self, onbellek_klasoru="onbellek"):
        
        self.onbellek_klasoru = os.path.join(os.getcwd(), onbellek_klasoru)
        
        #print(onbellek_klasoru)
        #print(self.onbellek_klasoru)
    
    # bugünün doviz kurlarını verir
    def bugunun_kurlari(self):
        bugun = date.today()
        return self.doviz_kurlari(bugun.day, bugun.month, bugun.year)
    
    # bugün haricindeki diğer günlerin kurlarını verir
    def doviz_kurlari(self, gun, ay, yil):
        bugun = date.today()
        
        klasor = str(yil) + self.__basta_sifir(ay)
        dosya = self.__basta_sifir(gun) + self.__basta_sifir(ay) + str(yil) + ".xml"
        
        if bugun.day == gun and bugun.month == ay and bugun.year == yil:
            url = "https://www.tcmb.gov.tr/kurlar/today.xml"
            onbellek_kullan = False
        else :
            url = "https://www.tcmb.gov.tr/kurlar/" + klasor + "/" + dosya
            onbellek_kullan = True
            
        if onbellek_kullan:
            # ön bellekten okumaya çalış.
            sonuc = self.__onbellekten_oku(klasor, dosya)
            
            if sonuc["durum"] == "OK":
                #ön bellekten okuma başarılı
                return self.__verileri_cozumle(sonuc["veri"])
            else:
                # ön bellekten okuma başarısız.
                sunucudan_veri = self.__sunucudan_veri_cek(url)
                if sunucudan_veri != None:
                    # ön belleğe yaz...
                    self.__onbellege_yaz(klasor, dosya, sunucudan_veri)
                    return self.__verileri_cozumle(sunucudan_veri)
                else:
                    self.__sonuc["durum"] = "ERROR"
                    self.__sonuc["mesaj"] = "Sunucundan veri çekilemedi. Ön bellek oluşturulamadı."
                    self.__sonuc["veri"] = {}
                    return self.__sonuc 
        else :
            veri = self.__sunucudan_veri_cek(url)
            if veri != None:
                # veri sağlıklı bir biçimde alındı.
                # artık veriyi işleyip yorumlayacağız.
                return self.__verileri_cozumle(veri)
            else:
                self.__sonuc["durum"] = "ERROR"
                self.__sonuc["mesaj"] = "Sunucundan veri çekilemedi."
                self.__sonuc["veri"] = {}
                return self.__sonuc
    
    # sunucudan veri çeker
    def __sunucudan_veri_cek(self, url):
        try:
            istek = requests.get(url)
            
            if istek.status_code == 200:
                return istek.content
            else:
                print("Sunucu 200 istek kodu göndermedi")
                return None
            
        except Exception as e:
            print("Sunucudan veri çekerken hata oldu. Bu da hata mesajı:", e)
            return None
    
    # çekilen veriyi ya da ön bellekten okunan veriyi yorumlar
    def __verileri_cozumle(self, veri):
        # önce sonuç-veri kısmını boşaltalım.
        self.__sonuc["veri"] = {}
        
        try:
            icerik = BeautifulSoup(veri, "xml")
            
            kurlar = icerik.find_all("Currency")
            
            for kur in kurlar:
                kod = kur.get("CurrencyCode") # USD, EUR, TRY gibi döviz kodunu veriyor.
                
                # değer xdr ise bunu atlayalım...
                if kod == "XDR":
                    continue
                
                isim = kur.find("Isim").text
                alis = kur.find("ForexBuying").text
                satis = kur.find("ForexSelling").text
                
                self.__sonuc["veri"][kod] = {"kod" : kod, "isim" : isim, "alis" : alis, "satis" : satis}
            
            self.__sonuc["durum"] = "OK"
            self.__sonuc["mesaj"] = "Veriler başarıyla çekildi ve yorumlandı"
            return self.__sonuc
        
        except Exception as e:
            self.__sonuc["durum"] = "ERROR"
            self.__sonuc["mesaj"] = "Verilerin getirilmesi sırasında sorun oluştu. Hata: " + str(e)
            self.__sonuc["veri"] = {}
            return self.__sonuc
    
    # ön bellekten okur
    def __onbellekten_oku(self, klasor, dosya):
        okunacak_dosya = os.path.join(self.onbellek_klasoru, klasor, dosya)
        if os.path.exists(okunacak_dosya):
            # okunacak dosya varmış. haydi okuyalım...
            try:
                with open(okunacak_dosya, "rb") as dosya:
                    self.__sonuc["durum"] = "OK"
                    self.__sonuc["mesaj"] = "Ön bellek dosyasından okuma başarılı."
                    self.__sonuc["veri"] = dosya.read()
                    return self.__sonuc
            except Exception as e:
                self.__sonuc["durum"] = "ERROR"
                self.__sonuc["mesaj"] = "Ön bellek dosyası okunurken bir hata oluştu. Hata: " + str(e)
                self.__sonuc["veri"] = {}
                return self.__sonuc
        else:
            self.__sonuc["durum"] = "ERROR"
            self.__sonuc["mesaj"] = "Ön bellek dosyası bulunamadı."
            self.__sonuc["veri"] = {}
            return self.__sonuc
    
    # ön belleğe yazar
    def __onbellege_yaz(self, klasor, dosya, veri):
        if not os.path.exists(os.path.join(self.onbellek_klasoru, klasor)):
            os.mkdir(os.path.join(self.onbellek_klasoru, klasor))
        
        try:
            with open(os.path.join(self.onbellek_klasoru, klasor, dosya), "wb") as dosya:
                dosya.write(veri)
        except Exception as e:
            print("HATA:", e)
                
            
    
    # 5 i 05 şekline döndüren fonksiyon
    def __basta_sifir(self, sayi):
        if sayi < 10:
            return "0" + str(sayi)
        else :
            return str(sayi)