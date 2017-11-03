function [f, fplus, HighHarm]=fastball_analysis(n,c,Fs,Dv,Sf,varargin)
% By A Milton, 2017
% This is made available in the hope that it is useful. Free to use and/or
% modify but comes with no warranty, guarantee or support.%
%% Prior conditions -
% 1. Files and this function should be contained in a separate folder with no extra '*.txt' files.
% 2. Separate .txt files for each participant and each condition (including
%    separate files for control conditions, if applicable) of the following type: Px_Cx.txt (e.g. P1_C3.txt).
% 3. File rows = time points and file columns = electrodes.
% Input:
%   Required
%   n       - number of participants
%   c       - number of conditions (including controls)
%   Fs      - sample rate (Hz)
%   Dv      - deviant/oddball frequency (Hz)
%   Sf      - standard stimulus frequency (Hz)
%   Optional
%   wh      - 2 number column vector for correction parameters: 1= width of SNR correction (0.45Hz default) MUST NOT be larger than Dv
%             2 = number of adjacent bins to ignore in correction (default = 1 = 1 either side);
%   ot      - Type of output - based on correction procedure:
%                           1 (default)= Signal-to-noise ratio/SNR. Amplitude of central bin divided by mean of surrounding bins. Harmonics averaged;
%                           2 = Corrected amplitude/CA. Amplitude of central bin subtracted by mean amplitude of surrounding bins. Harmonics summed.
%   dt      - 1 = de-trend and de-mean whole file; 0 (default) = do not.
%   lc      - If unsure data for all ppts is the same length/number of timepoints, this can
%             pre-process & make consistent (takes time). 1=Check; 0 (default)= don't.
% Output:
%   f       - Deviant frequency (SNR/CA - as chosen by input ot - default = SNR). Columns=Conditions,
%             Rows = 1:n = ppts 1:n for elec 1. n+1:2n= ppts 1:n for electrode 2... 
%   fplus   - Deviant+significant harmonics - organised in same way as f.
%   HighHarm- Highest Harmonic (row 1: Hz; row 2: number). Columns =
%             conditions.
%             NaN=deviant frequency itself not >3.29 so counts no further.

%% Housekeeping
% Default values
wh = [.45, 1];
ot = 1;
dt = 0;
lc = 0;
% Loading optional arguments
while ~isempty(varargin)
    switch lower(varargin{1})
          case 'wh'
              wh = varargin{2};
          case 'ot'
              ot = varargin{2};
          case 'dt'
              dt = varargin{2};
          case 'lc'
              lc = varargin{2};
          otherwise
              error(['Unexpected option: ' varargin{1}])
    end
    varargin(1:2) = [];
end

%Bodge for awkward Fs and Dv mix.
if mod(Fs/Dv, floor(Fs/Dv))>0; %if cannot resolve f in one window length
bam=mod(Fs/Dv, floor(Fs/Dv)).*[1:1000];YY=mod(bam,1)<.000001;B=0;
if sum(YY)==0;
error('Error. \nTo derive the amplitude at the exact frequency bin of the deviant frequency, \nthe window length of the data analysed needs to equal an integer \nnumber of cycles of the deviant frequency. \nGiven your sample rate and deviant frequency, %f sample points are needed per cycle of the deviant frequency. \nThis combination of sample rate and deviant frequency does not allow this.',Fs/Dv)
else
for o=1:size(bam,2);if YY(o)==1 && B==0;B=1;NCYC=o;end;end
warning('\nDue to Fs and Dv combination, your data may be trimmed by up to %0.1f cycles of the deviant frequency, which is %0.1f data points.',NCYC, Fs/Dv*NCYC);
minD=Fs/Dv*NCYC;%defines minimum number of data points needed to derive exact frequency bin for Dv
end
end

folder=cd;
files=dir('*.txt');
if lc==1;
    ds=zeros(numel(files),1);
    for FL=1:numel(files);
        dat=dlmread(files(FL).name);
        if mod(Fs/Dv, floor(Fs/Dv))==0;
        ds(FL,1)= size(dat,1)-mod( size(dat,1) , Fs/Dv );
        elseif mod(Fs/Dv, floor(Fs/Dv))>0;
            vminD=minD:minD:size(dat,1);
            ds(FL,1)=vminD(end);
        end
    end
end

%% First extract amplitude, SNR and z-scores for each condition & electrode
mkdir pptfiles
for FL=1:numel(files);
    snam=files(FL).name(1:end-4);
    dat=[]; dat=dlmread(files(FL).name);
    if lc==1;
        dat=dat(1:min(ds),:);
    elseif mod(Fs/Dv, floor(Fs/Dv))==0;
        dat=dat(1:end-mod( size(dat,1) , Fs/Dv ),:); %trim end of epoch if not integer length of deviant frequency
    elseif mod(Fs/Dv, floor(Fs/Dv))>0;
        vminD=minD:minD:size(dat,1);
        dat=dat(1:vminD(end),:);
    end
    Res=Fs/size(dat,1); %frequency resolution
    %de-trend & de-mean if desired
    if dt==1; dat=detrend(dat);end
    
    % FFT
    fBins=0:Res:Fs/2;
    AbsC=zeros(size(dat,2),size(dat,1)/2+1);
    for e=1:size(dat,2);
        eegFFT = fft(dat(:,e),size(dat,1));
        AbsC(e,:)=abs(eegFFT(1:size(dat,1)/2+1)/size(dat,1))*2;
    end
    AbsC=AbsC(:,2:end);
    fBins=fBins(2:end);    
    %Correction procedures (SNR,Z,BCA...)
    wdth=ceil(1/Res*wh(1));
    stp=wdth+wh(2)+1;
    SNRbins=fBins(stp:end-(stp-1)); %this defines actual bins used
    SNRvals=zeros(size(dat,2),size(SNRbins,2));CAvals=zeros(size(dat,2),size(SNRbins,2));Zvals=zeros(size(dat,2),size(SNRbins,2)); 
    for e=1:size(dat,2);
        for b=1:size(SNRbins,2);
            tmn=mean(AbsC(e,[((stp+(b-1))-(wdth+wh(2))):((stp+(b-1))-(wh(2)+1)),((stp+(b-1))+(wh(2)+1)):((stp+(b-1))+(wdth+wh(2)))]));
            tstd=std(AbsC(e,[((stp+(b-1))-(wdth+wh(2))):((stp+(b-1))-(wh(2)+1)),((stp+(b-1))+(wh(2)+1)):((stp+(b-1))+(wdth+wh(2)))]));
            Zvals(e,b)=(AbsC(e,stp+(b-1))-tmn)/tstd;
            SNRvals(e,b)=AbsC(e,stp+(b-1))/tmn; %ratio
            CAvals(e,b)=AbsC(e,stp+(b-1))-tmn; %subtraction
        end
    end
    %save values
    sdir=[folder '\pptfiles\'];
    Dnam1=[sdir snam '_SNRmatrix.txt'];
    dlmwrite(Dnam1,SNRvals,'\t');
    Dnam1=[sdir snam '_Zmatrix.txt'];
    dlmwrite(Dnam1,Zvals,'\t');
    Dnam1=[sdir snam '_AMPmatrix.txt'];
    dlmwrite(Dnam1,AbsC,'\t');
    Dnam1=[sdir snam '_CAmatrix.txt'];
    dlmwrite(Dnam1,CAvals,'\t');
    vdir=[sdir snam];
    save(vdir, 'SNRvals', 'Zvals', 'AbsC', 'CAvals', 'SNRbins', 'fBins')
    if FL==1;Dnam1=[sdir 'SNRbins.txt'];dlmwrite(Dnam1,SNRbins,'\t');Dnam1=[sdir 'AMPbins.txt'];dlmwrite(Dnam1,fBins,'\t');end
    %plot and save all channel plot (.tiff)
    [cvv, vindx]=min(abs(SNRbins-Sf*2));%plot up to 2*Standard stimulus frequency
    tx=figure(1);plot(SNRbins(1:vindx),mean(SNRvals(:,1:vindx)));set(gcf,'Color','w');box off
    set(gca,'XTick',Dv:Dv:Sf*2);
    xlabel('Frequency (Hz)','fontweight','bold','fontsize',7);
    ylabel('SNR','fontweight','bold','fontsize',7);
    title('All Channel Plot of SNR');
    set(tx,'PaperUnits','centimeters','PaperPosition',[0 0 12.5 8.5])
    Inam1=[sdir snam '_All_Channel'];
    print(Inam1,'-dtiffnocompression','-r300')
    set(tx,'PaperUnits','centimeters','PaperPosition',[0 0 12.5 8.5])
    close  
end
clear dat Zvals AbsC SNRvals CAvals files
%% Second - Harmonic calculation (derive f+)
oldFolder = cd(sdir);
fnam={};
for C=1:c;
tt=['*C' num2str(C) '.mat'];
fnam{C,1}=tt;
end
HighHarm=zeros(2,size(fnam,1));
Hmc=Dv:Dv:SNRbins(end); Hmc(2:c+1,:)=0; %creates all harmonics from deviant 
for h=1:size(fnam,1); %condition loop
    files=dir(fnam{h}); %read only AMP matrix files at the moment
    %load up all ppts into a 3D matrix
    for FL=1:numel(files);
        j=load(files(FL).name,'AbsC');
        dat(:,:,FL)=j.AbsC;
    end
    GA=mean(dat,3); %generate Grand Average amplitude for each electrode
    %first, collapse GA amplitudes across ALL channels
    TotalGA=mean(GA);
    TotalGAZ=zeros(1,size(SNRbins,2)); %matrix for All-channel Grand Average Z-score
    for b=1:size(SNRbins,2);              
                tmn=mean(TotalGA(1,[((stp+(b-1))-(wdth+wh(2))):((stp+(b-1))-(wh(2)+1)),((stp+(b-1))+(wh(2)+1)):((stp+(b-1))+(wdth+wh(2)))]));
                tstd=std(TotalGA(1,[((stp+(b-1))-(wdth+wh(2))):((stp+(b-1))-(wh(2)+1)),((stp+(b-1))+(wh(2)+1)):((stp+(b-1))+(wdth+wh(2)))]));
                TotalGAZ(1,b)=(TotalGA(1,stp+(b-1))-tmn)/tstd;
    end 
    %calculate highest deviant harmonic significant
    Avd=zeros(1,size(Hmc,2)); Avd(1,Sf/Dv:Sf/Dv:end)=1;
    frst=0;
    for j=1:size(Hmc,2);
        [cvv, vindx]=min(abs(SNRbins-Hmc(1,j)));
        Hmc(h+1,j)=TotalGAZ(vindx); 
        if Hmc(h+1,j)<3.29 && j==1;
            frst=1;HighHarm(1:2,h)=NaN;
        end
        if Hmc(h+1,j)<3.29 && frst==0 && j>1 && Avd(j)==0;
            HighHarm(1,h)=ctr; % Hz
            HighHarm(2,h)=j-1; % #
            frst=1;
        end
        if j==size(Hmc,2) && frst==0 && Avd(j)==0;
             HighHarm(1,h)=Hmc(1,j); % Hz
             HighHarm(2,h)=j; % #
        end
        if Avd(j)==0;ctr=Hmc(1,j);end
    end  
end
dlmwrite('HIGHEST_HARMONIC_GA.txt',HighHarm,'\t');
dlmwrite('HARMONIC_GA_Zscores.txt',Hmc,'\t');

%% Third - generate final file
typ={'SNRvals','CAvals'};
f=zeros(n*size(dat,1),c); %output
fplus=zeros(n*size(dat,1),c); %output
for h=1:size(fnam,1); %condition loop
    files=dir(fnam{h}); %read only AMP matrix files at the moment
    %load up all ppts into a 3D matrix
    dat=[];
    for FL=1:numel(files);
        j=load(files(FL).name,typ{ot});
        if ot==1;
        dat(:,:,FL)=j.SNRvals;
        elseif ot==2;
            dat(:,:,FL)=j.CAvals;
        end
    end
    HMC=[];
    if isnan(HighHarm(2,h));%No harmonics 
    HMC=Hmc(1,1);
    else % #Harmonics
        for vh=1:HighHarm(2,h);
            if Avd(1,vh)==0;
                HMC=[HMC,Hmc(1,vh)];
            end
        end
    end
    for P=1:size(dat,3);%ppt;
        for E=1:size(dat,1); %electrode
            tempD=zeros(1,size(HMC,2));
            for j=1:size(HMC,2); %
                [cvv, vindx]=min(abs(SNRbins-HMC(1,j)));
                tempD(1,j)=dat(E,vindx,P);
            end
            if ot==2; fplus((E-1)*n+P,h)=sum(tempD);
            elseif ot==1; fplus((E-1)*n+P,h)=mean(tempD);end%
            f((E-1)*n+P,h)=tempD(1);%deviant freq only
        end
    end
end
dlmwrite('f_Deviant_Output.txt',f,'\t');
dlmwrite('f+_DeviantHarmonics_Output.txt',fplus,'\t');
end

function dat=detrend(dat)
    %detrend whole data w/bivariate linear regression
    x=zeros(size(dat,1),1);
    for lgth=1:size(dat,1);
        x(lgth,1)=lgth/size(dat,1);
    end
    tempdat=zeros(size(dat,1),size(dat,2));
    for e=1:size(dat,2);
        byx=(sum((x-mean(x)).*(dat(:,e)-mean(dat(:,e)))))/sum((x-mean(x)).^2);
        lrctr=1;
        for tpl=1:size(dat,1);                       
            tempdat(tpl,e)=dat(tpl,e)-x(lrctr)*byx;
            lrctr=lrctr+1;
        end
        %de-mean
        tempdat(:,e)=tempdat(:,e)-mean(tempdat(:,e));
    end     
    dat=tempdat;
end