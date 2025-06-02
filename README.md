# Drone Filo Optimizasyonu: Çok Kısıtlı Ortamlarda Dinamik Teslimat Planlaması

## Proje Özeti
  Bu proje, Kocaeli Üniversitesi Teknoloji Fakültesi Bilişim Sistemleri Mühendisliği Bölümü'nün TBL331: Yazılım Geliştirme Laboratuvarı II dersi kapsamında Grup 2 öğrencileri tarafından geliştirilmiştir. Enerji limitleri ve uçuş yasağı bölgeleri (no-fly zone) gibi dinamik kısıtlar altında çalışan drone'lar için en uygun teslimat rotalarının belirlenmesini sağlayan bir algoritma tasarlamayı hedeflemektedir. Proje kapsamında, teslimat noktaları, drone özellikleri ve operasyonel kısıtlar esnek bir yapıda tanımlanmakta ve gerektiğinde rastgele olarak A*, Genetik Algoritma (GA) ve Kısıt Tatmini Problemi (CSP) ile üretilebilmektedir. Bu sayede, gerçek zamanlı koşullarda drone filo yönetimi için yenilikçi ve uyarlanabilir bir çözüm geliştirilmesi amaçlanmaktadır.
  
## Proje İçeriği
* Teslimat Sistemleri: Drone'ların kapasiteleri, teslimat noktaları ve uçuşa yasak bölgeler dahil edilerek operasyonel verimlilik sağlanmaktadır.
* Optimizasyon Yöntemleri: A*, CSP ve GA kullanılarak en uygun teslimat rotaları belirlenmektedir.
* Modelleme ve Simülasyon: Grafik teorisi bazlı modelleme ile algoritmaların performansı test edilmekte ve görselleştirilmektedir.
* Dinamik Teslimat Planlaması: Gerçek zamanlı değişkenler ışığında sürekli güncellenen rotalar oluşturulmaktadır.
* Zaman Karmaşıklığı Analizi: Algoritmaların performans metrikleri ve işlem süreleri detaylı olarak değerlendirilmiştir.

## Geliştirme Ortamı
Proje aşağıdaki temel teknolojiler ve kütüphaneler kullanılarak geliştirilmiştir:

* *Programlama Dili:* Python
* *Kütüphaneler:*
    * matplotlib: Teslimat rotalarının ve drone hareketlerinin harita üzerinde görselleştirilmesi için kullanılmıştır.
    * networkx: A* algoritmasını çalıştırabilmek için kullanılmıştır.
    * numpy:Matematiksel hesaplamalar için kullanılmıştır.
 
## Projenin Kurulumu

Projeyi yerel makinenize kurmak ve çalıştırmak için aşağıdaki adımları izleyin:

1.  *Depoyu Klonlayın:*
    bash
    git clone https://github.com/NecibeGuner/drone-fleet-optimization.git
    
    cd DroneFiloOptimisation
    

2.  *Gerekli Kütüphaneleri Yükleyin:*
    bash
    pip install -r requirements.txt
    
 
  ## 📊 Çıktılar
Proje çalıştırıldığında görülmesi gereken çıktılar
* Görselleştirilmiş rota haritaları 🗺 
* Tamamlanan teslimat yüzdesi 📦 
* Enerji tüketim analizi ⚡ 
* Algoritma çalışma süreleri ⏱ 
 
## Algoritmaların Karşılaştırılması ve Zaman Karmaşıklığı Analizi
Drone filo optimizasyonuna yönelik geliştirilen sistemin gerçek zamanlı uygulanabilirliğini değerlendirebilmek için algoritmaların zaman karmaşıklığı hem teorik hem de deneysel olarak analiz edilmesi gerekmektedir. Özellikle dinamik kısıtların (örneğin uçuş yasağı bölgeleri, batarya sınırlamaları ve öncelikli teslimatlar) sisteme entegre edilmesi, algoritmaların işlem süresi üzerindeki etkisini doğrudan artırmakta; bu durum, zaman verimliliğini kritik bir metrik hâline getirmektedir.

Projede rota optimizasyonu için A* algoritması ve Genetik Algoritma (GA) kullanılmıştır. A* algoritması, belirli bir hedefe en kısa yolu bulmada etkili olup, sezgisel bir arama yöntemidir. GA ise daha geniş ve dinamik problem uzaylarında global optimumu bulma potansiyeline sahip, popülasyon tabanlı bir optimizasyon tekniğidir. Bu algoritmaların karmaşıklığı raporda belirtilmiştir.

## Proje Raporu
📎 [Proje Raporunu Görüntüle veya İndir](https://github.com/NecibeGuner/drone-fleet-optimization/raw/main/grup_2.docx)


## Trello Linki
[drone-fleet-optimization-trello](https://trello.com/invite/b/682881c2165431d88d4b4fb9/ATTIe847ffdf1f6c3e0153e7e4f7653609059A19D616/drone-fleet-optimization)
